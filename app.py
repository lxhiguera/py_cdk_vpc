#!/usr/bin/env python3

from aws_cdk import core

from py_cdk_vpc.py_cdk_vpc_stack import PyCdkVpcStack


app = core.App()
PyCdkVpcStack(app, "py-cdk-vpc")

app.synth()
