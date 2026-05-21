import boto3

client = boto3.client('cognito-idp')

def lambda_handler(event, context):
    user_pool_id = event['userPoolId']
    username = event['userName']
    
    group_name = 'Analysts'
    
    try:
        # Ensure the group exists
        try:
            client.get_group(UserPoolId=user_pool_id, GroupName=group_name)
        except client.exceptions.ResourceNotFoundException:
            client.create_group(
                UserPoolId=user_pool_id,
                GroupName=group_name,
                Description='Default group for automatically confirmed users'
            )
            print(f"Created group {group_name}")
            
        # Add the user to the group
        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"Successfully added {username} to {group_name}")
        
    except Exception as e:
        print(f"Error adding user to group: {e}")
        
    # Return the event to Cognito so it can proceed
    return event
