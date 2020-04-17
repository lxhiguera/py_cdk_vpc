import ipaddress as ip
from aws_cdk import (
    aws_ec2 as _ec2,
    aws_iam as iam,
    core
)


class PyCdkVpcStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, stage={}, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # parameters from context
        customer = self.node.try_get_context("customer")
        namestage = stage['name_stage']
        vpccidr = stage['vpc_cidr']  # VPC CIDR
        vpcname = "vpc-" + customer + "-" + namestage
        subnetprefix = int(stage['subnet_prefix'])  # Subnets Prefix /XX
        maxazs = int(stage['max_azs'])  # Nro of AZs 
        layers = stage['layers']  # Names for Layers
        layerendpoints = stage['layer_endpoints']  # Layer name for Endpoints
        layersnat = stage['layer_nats']  # Layer name for the Nat Subnets
        activeflowlogs = stage['active_flowlogs']  # Active flowlogs?

        # flags subnets types
        flg_public = False
        flg_private = False
        flg_isolated = False

        # TODO: HANDLE ERROR for insuficient space to layers in VPC CIDR Space
        nro_subnets = len(layers.keys()) * maxazs
        subnets = list(ip.ip_network(vpccidr).subnets(new_prefix=subnetprefix))

        # subnets configuration - layeres * azs
        subnetsconfs = []
        for layer in layers:
            layertype = layers[layer]
            if layertype == 'PUBLIC':
                sntype = _ec2.SubnetType.PUBLIC
                flg_public = True
            if layertype == 'PRIVATE':
                sntype = _ec2.SubnetType.PRIVATE
                flg_private = True
            if layertype == 'ISOLATED':
                flg_isolated = True
                sntype = _ec2.SubnetType.ISOLATED
            subnetsconfs.append(_ec2.SubnetConfiguration(name=layer, subnet_type=sntype, cidr_mask=subnetprefix))

        # selection subnets nat
        natsubnets = None
        if layersnat in layers and layers[layersnat] == 'PUBLIC':
            natsubnets = _ec2.SubnetSelection(subnet_group_name=layersnat)

        # vpc tenacy
        vpctenacy = _ec2.DefaultInstanceTenancy.DEFAULT
        if self.node.try_get_context("vpc_tenacy") == 'DEDICATED':
            vpctenacy = _ec2.DefaultInstanceTenancy.DEDICATED

        # creation vpc
        sn_layer_endpoints = [_ec2.SubnetSelection(one_per_az=True, subnet_group_name=layerendpoints)]

        vpc = _ec2.Vpc(
            self,
            vpcname,
            max_azs=maxazs,
            cidr=vpccidr,
            subnet_configuration=subnetsconfs,
            nat_gateway_subnets=natsubnets,
            default_instance_tenancy=vpctenacy,
            gateway_endpoints={
                "S3": _ec2.GatewayVpcEndpointOptions(
                    service=_ec2.GatewayVpcEndpointAwsService.S3,
                    subnets=sn_layer_endpoints
                )
            }
        )

        # Config Route Tables
        # TODO: create RT by subnets type

        publicsubnets = vpc.select_subnets(subnet_type=_ec2.SubnetType.PUBLIC) if flg_public else ""
        privatesubnets = vpc.select_subnets(subnet_type=_ec2.SubnetType.PRIVATE) if flg_private else ""
        isolatedsubnets = vpc.select_subnets(subnet_type=_ec2.SubnetType.ISOLATED) if flg_isolated else ""

        # Endpoints
        # s3 Endpoint
        print(layerendpoints)
        sn_layer_endpoints = _ec2.SubnetSelection(one_per_az=True, subnet_group_name=layerendpoints)
        #vpc.add_s3_endpoint(vpcname+"-S3Endpoint",subnets=sn_layer_endpoints)
        #vpc.add_gateway_endpoint(vpcname + "-S3Endpoint", service=_ec2.GatewayVpcEndpointAwsService.S3,
        #                         subnets=sn_layer_endpoints)

        
        # ec2 endpoint
        ec2_endpoint = vpc.add_interface_endpoint(vpcname + "-ec2_endpoint",
                                                  service=_ec2.InterfaceVpcEndpointAwsService.E_C2,
                                                  subnets=sn_layer_endpoints)
        ec2_endpoint.connections.allow_from_any_ipv4(
            port_range=_ec2.Port(from_port=443, to_port=443, protocol=_ec2.Protocol.TCP, string_representation="https"))

        # ec2 messages endpoint
        ec2messages_endpoint = vpc.add_interface_endpoint(vpcname + "-ec2message_endpoint",
                                                          service=_ec2.InterfaceVpcEndpointAwsService.E_C2_MESSAGES,
                                                          subnets=sn_layer_endpoints)
        ec2messages_endpoint.connections.allow_from_any_ipv4(
            port_range=_ec2.Port(from_port=443, to_port=443, protocol=_ec2.Protocol.TCP, string_representation="https"))

        # ssm endpoint
        ssm_endpoint = vpc.add_interface_endpoint(vpcname + "-ssm_endpoint",
                                                  service=_ec2.InterfaceVpcEndpointAwsService.SSM,
                                                  subnets=sn_layer_endpoints)
        ssm_endpoint.connections.allow_from_any_ipv4(
            port_range=_ec2.Port(from_port=443, to_port=443, protocol=_ec2.Protocol.TCP, string_representation="https"))

        # ssm messages endpoint
        ssmmessages_endpoint = vpc.add_interface_endpoint(vpcname + "-ssmmessages_endpoint",
                                                          service=_ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
                                                          subnets=sn_layer_endpoints)
        ssmmessages_endpoint.connections.allow_from_any_ipv4(
            port_range=_ec2.Port(from_port=443, to_port=443, protocol=_ec2.Protocol.TCP, string_representation="https"))

        # SSM IAM Role
        ec2_ssm_iam_role = iam.Role(self, "ssm_ec2_iam_role", assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),role_name="ssm_ec2_iam_role_"+stage['name_stage'])
        ec2_ssm_iam_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonEC2RoleforSSM'))
        ec2_ssm_iam_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchAgentServerPolicy'))
        #add Role to instance profile
        iam.CfnInstanceProfile(self,"instance_profile",roles=["ssm_ec2_iam_role_"+stage['name_stage']],instance_profile_name="ssm_ec2_iam_role_"+stage['name_stage'])

        #add polices to iam role
        ec2_ssm_iam_role.add_to_policy(iam.PolicyStatement(
            resources=["arn:aws:s3:::aws-ssm-" + self.region + "/*",
                       "arn:aws:s3:::aws-windows-downloads-" + self.region + "/*",
                       "arn:aws:s3:::amazon-ssm-" + self.region + "/*",
                       "arn:aws:s3:::amazon-ssm-packages-" + self.region + "/*",
                       "arn:aws:s3:::" + self.region + "-birdwatcher-prod/*",
                       "arn:aws:s3:::patch-baseline-snapshot-" + self.region + "/*"],
            actions=["s3:GetObject"]
        ))

        ec2_ssm_iam_role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["ssmmessages:CreateControlChannel",
                     "ssmmessages:CreateDataChannel",
                     "ssmmessages:OpenControlChannel",
                     "ssmmessages:OpenDataChannel",
                     "s3:GetEncryptionConfiguration",
                     "kms:Decrypt"]
        ))
