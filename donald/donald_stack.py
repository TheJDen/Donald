from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_lambda as lambda_,
    aws_iam
)
from constructs import Construct


class DonaldStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        docker_function = lambda_.DockerImageFunction(
            self,
            "DockerFunction",
            code=lambda_.DockerImageCode.from_image_asset("./src"),
            memory_size=1024,
            timeout=Duration.seconds(10),
            architecture=lambda_.Architecture.ARM_64,
        )

        docker_function.add_to_role_policy(
            aws_iam.PolicyStatement.from_json({
                "Effect": "Allow",
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "arn:aws:secretsmanager:us-east-1:736272884131:secret:DonaldDiscord-47vyvz"
                })
            )

        function_url = docker_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors={
                "allowed_origins": ["*"],
                "allowed_methods": [lambda_.HttpMethod.ALL],
                "allowed_headers": ["*"],
            },
        )

        CfnOutput(
            self, "FunctionUrl",
            value=function_url.url,
        )
