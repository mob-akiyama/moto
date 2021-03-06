from __future__ import unicode_literals
import json

from mock import patch
import sure  # noqa

from moto.cloudformation.models import FakeStack
from moto.cloudformation.parsing import resource_class_from_type
from moto.sqs.models import Queue
from boto.cloudformation.stack import Output
from boto.exception import BotoServerError

dummy_template = {
    "AWSTemplateFormatVersion": "2010-09-09",

    "Description": "Create a multi-az, load balanced, Auto Scaled sample web site. The Auto Scaling trigger is based on the CPU utilization of the web servers. The AMI is chosen based on the region in which the stack is run. This example creates a web service running across all availability zones in a region. The instances are load balanced with a simple health check. The web site is available on port 80, however, the instances can be configured to listen on any port (8888 by default). **WARNING** This template creates one or more Amazon EC2 instances. You will be billed for the AWS resources used if you create a stack from this template.",

    "Resources": {
        "Queue": {
            "Type": "AWS::SQS::Queue",
            "Properties": {
                "QueueName": "my-queue",
                "VisibilityTimeout": 60,
            }
        },
    },
}

name_type_template = {
    "AWSTemplateFormatVersion": "2010-09-09",

    "Description": "Create a multi-az, load balanced, Auto Scaled sample web site. The Auto Scaling trigger is based on the CPU utilization of the web servers. The AMI is chosen based on the region in which the stack is run. This example creates a web service running across all availability zones in a region. The instances are load balanced with a simple health check. The web site is available on port 80, however, the instances can be configured to listen on any port (8888 by default). **WARNING** This template creates one or more Amazon EC2 instances. You will be billed for the AWS resources used if you create a stack from this template.",

    "Resources": {
        "Queue": {
            "Type": "AWS::SQS::Queue",
            "Properties": {
                "VisibilityTimeout": 60,
            }
        },
    },
}

output_dict = {
    "Outputs": {
        "Output1": {
            "Value": {"Ref": "Queue"},
            "Description": "This is a description."
        }
    }
}

bad_output = {
    "Outputs": {
        "Output1": {
            "Value": {"Fn::GetAtt": ["Queue", "InvalidAttribute"]}
        }
    }
}

get_attribute_output = {
    "Outputs": {
        "Output1": {
            "Value": {"Fn::GetAtt": ["Queue", "QueueName"]}
        }
    }
}

outputs_template = dict(list(dummy_template.items()) + list(output_dict.items()))
bad_outputs_template = dict(list(dummy_template.items()) + list(bad_output.items()))
get_attribute_outputs_template = dict(list(dummy_template.items()) + list(get_attribute_output.items()))

dummy_template_json = json.dumps(dummy_template)
name_type_template_json = json.dumps(name_type_template)
output_type_template_json = json.dumps(outputs_template)
bad_output_template_json = json.dumps(bad_outputs_template)
get_attribute_outputs_template_json = json.dumps(get_attribute_outputs_template)


def test_parse_stack_resources():
    stack = FakeStack(
        stack_id="test_id",
        name="test_stack",
        template=dummy_template_json,
        region_name='us-west-1')

    stack.resource_map.should.have.length_of(1)
    list(stack.resource_map.keys())[0].should.equal('Queue')
    queue = list(stack.resource_map.values())[0]
    queue.should.be.a(Queue)
    queue.name.should.equal("my-queue")


@patch("moto.cloudformation.parsing.logger")
def test_missing_resource_logs(logger):
    resource_class_from_type("foobar")
    logger.warning.assert_called_with('No Moto CloudFormation support for %s', 'foobar')


def test_parse_stack_with_name_type_resource():
    stack = FakeStack(
        stack_id="test_id",
        name="test_stack",
        template=name_type_template_json,
        region_name='us-west-1')

    stack.resource_map.should.have.length_of(1)
    list(stack.resource_map.keys())[0].should.equal('Queue')
    queue = list(stack.resource_map.values())[0]
    queue.should.be.a(Queue)


def test_parse_stack_with_outputs():
    stack = FakeStack(
        stack_id="test_id",
        name="test_stack",
        template=output_type_template_json,
        region_name='us-west-1')

    stack.output_map.should.have.length_of(1)
    list(stack.output_map.keys())[0].should.equal('Output1')
    output = list(stack.output_map.values())[0]
    output.should.be.a(Output)
    output.description.should.equal("This is a description.")


def test_parse_stack_with_get_attribute_outputs():
    stack = FakeStack(
        stack_id="test_id",
        name="test_stack",
        template=get_attribute_outputs_template_json,
        region_name='us-west-1')

    stack.output_map.should.have.length_of(1)
    list(stack.output_map.keys())[0].should.equal('Output1')
    output = list(stack.output_map.values())[0]
    output.should.be.a(Output)
    output.value.should.equal("my-queue")


def test_parse_stack_with_bad_get_attribute_outputs():
    FakeStack.when.called_with(
        "test_id", "test_stack", bad_output_template_json, "us-west-1").should.throw(BotoServerError)
