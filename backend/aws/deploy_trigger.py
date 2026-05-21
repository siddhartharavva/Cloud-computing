import boto3
import json
import os
import time
import zipfile
from dotenv import load_dotenv

load_dotenv("/Users/siddhartharavva/Desktop/Cloud Computing Proj/Cloud-computing/.env")

region = os.getenv("AWS_REGION", "eu-north-1")
pool_id = os.getenv("COGNITO_USER_POOL_ID")

iam = boto3.client("iam", region_name=region)
lmb = boto3.client("lambda", region_name=region)
cognito = boto3.client("cognito-idp", region_name=region)

role_name = "ZeroTrustCognitoTriggerRole"
lambda_name = "ZeroTrustAutoGroupAssign"

print("Creating IAM Role for Lambda...")
assume_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow"}]
}

try:
    role_response = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_role_policy)
    )
    role_arn = role_response["Role"]["Arn"]
    print("Role created:", role_arn)
    time.sleep(10) # wait for role to propagate
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)["Role"]["Arn"]
    print("Role already exists:", role_arn)

# Attach policies
iam.attach_role_policy(RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
iam.put_role_policy(
    RoleName=role_name,
    PolicyName="CognitoAdminAccess",
    PolicyDocument=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:AdminAddUserToGroup",
                    "cognito-idp:GetGroup",
                    "cognito-idp:CreateGroup"
                ],
                "Resource": f"arn:aws:cognito-idp:{region}:*:userpool/{pool_id}"
            }
        ]
    })
)

print("Packaging Lambda function...")
zip_path = "/tmp/lambda_function.zip"
with zipfile.ZipFile(zip_path, 'w') as z:
    z.write("/Users/siddhartharavva/Desktop/Cloud Computing Proj/Cloud-computing/backend/aws/cognito_post_confirmation.py", arcname="lambda_function.py")

with open(zip_path, "rb") as f:
    zip_bytes = f.read()

print("Creating/Updating Lambda function...")
try:
    lmb_response = lmb.create_function(
        FunctionName=lambda_name,
        Runtime="python3.11",
        Role=role_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_bytes},
        Timeout=10
    )
    func_arn = lmb_response["FunctionArn"]
    print("Created Lambda:", func_arn)
except lmb.exceptions.ResourceConflictException:
    lmb.update_function_code(FunctionName=lambda_name, ZipFile=zip_bytes)
    func_arn = lmb.get_function(FunctionName=lambda_name)["Configuration"]["FunctionArn"]
    print("Updated Lambda:", func_arn)

print("Granting Cognito permission to invoke Lambda...")
try:
    lmb.add_permission(
        FunctionName=lambda_name,
        StatementId="AllowCognitoInvoke",
        Action="lambda:InvokeFunction",
        Principal="cognito-idp.amazonaws.com",
        SourceArn=f"arn:aws:cognito-idp:{region}:{role_arn.split(':')[4]}:userpool/{pool_id}"
    )
except lmb.exceptions.ResourceConflictException:
    pass # Already granted

print("Configuring Cognito User Pool Trigger...")
pool_config = cognito.describe_user_pool(UserPoolId=pool_id)["UserPool"]
lambda_config = pool_config.get("LambdaConfig", {})
lambda_config["PostConfirmation"] = func_arn

kwargs = {
    "UserPoolId": pool_id,
    "LambdaConfig": lambda_config,
}
for key in ["Policies", "AutoVerifiedAttributes", "SmsVerificationMessage", "EmailVerificationMessage", "EmailVerificationSubject", "VerificationMessageTemplate", "SmsAuthenticationMessage", "MfaConfiguration", "DeviceConfiguration", "EmailConfiguration", "SmsConfiguration", "UserPoolTags", "AdminCreateUserConfig", "UserPoolAddOns", "AccountRecoverySetting"]:
    if key in pool_config:
        kwargs[key] = pool_config[key]

cognito.update_user_pool(**kwargs)
print("Trigger configured successfully!")
