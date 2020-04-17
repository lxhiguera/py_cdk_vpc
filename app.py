#!/usr/bin/env python3

from aws_cdk import core

from py_cdk_vpc.py_cdk_vpc_stack import PyCdkVpcStack


app = core.App()

customers = app.node.try_get_context("customer")
prod_stage = app.node.try_get_context("prod")
qa_stage = app.node.try_get_context("qa")
dev_stage = app.node.try_get_context("dev")
shared_stage = app.node.try_get_context("shared")


#PyCdkVpcStack(app, "production", env=core.Environment(account=prod_stage['account_id'],   region="us-east-1"), stage=prod_stage)
PyCdkVpcStack(app, "development", env=core.Environment(account=dev_stage['account_id'],   region="us-east-2"), stage=dev_stage)
#PyCdkVpcStack(app, "qa", env=core.Environment(account=qa_stage['account_id'],   region="us-east-1"), stage=qa_stage)
#PyCdkVpcStack(app, "shared", env=core.Environment(account=shared_stage['account_id'],   region="us-east-1"), stage=shared_stage)
app.synth()
