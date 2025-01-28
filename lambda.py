import os
import boto3
import json

# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
runtime = boto3.client('runtime.sagemaker')
sns = boto3.client('sns')

def lambda_handler(event, context):
    try:
        # Extract payload from event
        payload = json.loads(event['body'])  # Assuming 'body' contains the input data
        payload_data = payload.get('features')  # Adjust according to the structure of the input

        if not payload_data:
            raise ValueError("Missing 'features' in the payload")

        # Convert the payload to CSV format (or ensure it's the correct format for your model)
        # This step is critical if your model expects CSV input
        payload_csv = ','.join(map(str, payload_data))

        # Invoke the SageMaker endpoint
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',  # Make sure your model expects this format
            Body=payload_csv
        )

        # Process the response from SageMaker
        result = json.loads(response['Body'].read().decode())  # Decode response to JSON

        # Prepare prediction result
        preds = {"Prediction": result}

        # Create response dict
        response_dict = {
            "statusCode": 200,
            "body": json.dumps(preds)
        }

        # Publish result to SNS
        sns_message = json.dumps(response_dict)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Lambda Function Notification',
            Message=sns_message
        )

        return response_dict

    except Exception as e:
        # Handle errors
        error_message = str(e)
        response_dict = {
            "statusCode": 400,
            "body": json.dumps({"error": error_message})
        }

        sns_message = json.dumps(response_dict)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Lambda Function Error',
            Message=sns_message
        )

        return response_dict