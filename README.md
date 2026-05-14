# Step-by-Step Manual Setup Guide for Serverless Image Compressor

This guide will walk you through setting up the Cloud-Native Image Compressor from scratch using AWS services.

## Step 1: Set up S3 Buckets
1. Go to the AWS S3 Console.
2. Create an Input Bucket (e.g., `image-compressor-input-YOURNAME`). Leave default settings.
3. Create an Output Bucket (e.g., `image-compressor-output-YOURNAME`). Leave default settings.
4. Create a Frontend Hosting Bucket (e.g., `image-compressor-frontend-YOURNAME`). Enable static website hosting, unblock all public access, and attach a bucket policy that allows `s3:GetObject` for the public.

## Step 2: Set up IAM Role for Lambda
1. Go to the AWS IAM Console -> Roles.
2. Create a new Role for AWS Lambda.
3. Attach the following policies:
   - `AWSLambdaBasicExecutionRole` (for CloudWatch logs)
   - `AmazonS3FullAccess` (or custom policies allowing GetObject/PutObject on your specific buckets)

## Step 3: Create the Image Processor Lambda Function
1. Go to the AWS Lambda Console.
2. Create a new function: "ImageProcessorFunction". Choose Python 3.9+ as the runtime.
3. Assign the IAM Role created in Step 2.
4. Under "Code", copy and paste the contents of `lambda/Lambda code.py`.
5. Under "Configuration" -> "Environment variables", add:
   - Key: `OUTPUT_BUCKET`, Value: `image-compressor-output-YOURNAME`
6. Under "Configuration" -> "General configuration", increase Timeout to 1 minute and Memory to 256MB.
7. Click "Deploy".
8. **Add Pillow (PIL) Layer:** Since the Lambda needs Pillow to process images, scroll to the bottom of the function overview, click "Add a layer", provide the ARN for a public Pillow layer matching your Python version, or upload the zip file.
9. **Add S3 Trigger:** On the function overview, click "Add trigger", select S3, choose your Input Bucket, and set Event type to `All object create events`. Save.

## Step 4: Create the API Lambda Function
1. In the Lambda Console, create another new function: "APIHandlerFunction" with Python 3.9+.
2. Assign the same IAM Role.
3. Under "Code", copy and paste the contents of `lambda/Lambda code API.py`.
4. Under "Configuration" -> "Environment variables", add:
   - Key: `INPUT_BUCKET`, Value: `image-compressor-input-YOURNAME`
   - Key: `OUTPUT_BUCKET`, Value: `image-compressor-output-YOURNAME`
5. Click "Deploy".

## Step 5: Set up API Gateway
1. Go to the AWS API Gateway Console.
2. Create a new "HTTP API" (or REST API depending on your preference).
3. Create a Route: POST `/optimize` (and GET if you are polling results).
4. For the integration, select "Lambda" and choose the "APIHandlerFunction".
5. Go to "CORS" settings and configure it to allow all origins (`*`), allow headers (Content-Type), and allow methods (GET, POST, OPTIONS).
6. Deploy the API and copy the Invoke URL (e.g., `https://ke3a91dqwe.execute-api.ap-south-1.amazonaws.com/prod`).

## Step 6: Configure the Frontend
1. Open the `script.js` (and `app.js` if necessary) on your local machine.
2. Find the variable `API_BASE_URL` or `apiUrl` and update it with the API Gateway Invoke URL from Step 5.
   Example: `const API_BASE_URL = 'https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/prod';`
3. Save the changes.

## Step 7: Deploy the Frontend to S3
1. Go back to the S3 Console and open your Frontend Hosting Bucket.
2. Upload `index.html`, `style.css`, `script.js`, `app.js`, and the `Screenshots` folder.
3. In the bucket properties under Static Website Hosting, copy the Bucket Website Endpoint URL.

## Step 8: Test Your Application
1. Open your S3 Bucket Website Endpoint URL in your browser.
2. Upload an image.
3. Verify that the frontend gets the presigned URL, uploads it to the S3 Input Bucket, which triggers the Processor Lambda.
4. The Processor Lambda compresses it and puts it in the Output Bucket.
5. The frontend polls or retrieves the compressed image via API Gateway and shows the final result!
