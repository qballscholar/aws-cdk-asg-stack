#!/usr/bin/env python3

import base64 
from aws_cdk import (
    aws_autoscaling as autoscaling,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    App, CfnOutput, Stack
)

class LoadBalancingStack(Stack):
    def __init__(self, app: App, id: str) -> None:
        super().__init__(app, id)
        vpc=ec2.Vpc(self, "VPC")
        data=open("./httpd.sh","rb").read()
        httpd=ec2.UserData.for_linux()
        httpd.add_commands(str(data, "utf-8"))
        
        # This block of code defines the auto scaling group resource. Parameters include the ID or name, VPC, instance_type, machine_image or AMI, and the user_data.
        asg = autoscaling.AutoScalingGroup (
            self, 
            "ASG", 
            vpc=vpc, 
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2, ec2.Instance.MICRO
            ),
            machine_image=ec2.AmazonLinuxImage (generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            user_data=httpd,
        )
        
        # This block of code defines the load balancer resource. The method ApplicationLoadBalancer states the type of load balancer to use. Parameters include the ID or name, VPC, and a boolean value to state if this will be internet_facing (public) or not.
        lb = elbv2.ApplicationLoadBalancer(
            self,
            "LB",
            vpc=vpc,
            internet_facing=True)        
        
        # These next few lines of code configures the listener properties of the load balancer. It also defines the targets to send traffic to.
        listener=lb.add_listener("Listener", port=80)
        listener.add_targets("Target", port=80, targets=[asg])
        listener.connections.allow_default_port_from_any_ipv4("Open to the world")
        
        # The first line provides other configuration settings for the auto scaling group resource created earlier. The second line creates a CfnOutput for the stack.
        asg.scale_on_request_count("AModestLoad", target_request_per_minute=60)
        CfnOutput(self, "LoadBalancer", export_name="LoadBalancer", value=lb.load_balancer_dns_name)
        
        # Here the LoadBalancerStack class is called and executed. After the app is executed, synth causes the resources defined to be translated into an AWS CloudFormation template.
        app = App()
        LoadBalancingStack(app, "LoadBalancingStack")
        app.synth()