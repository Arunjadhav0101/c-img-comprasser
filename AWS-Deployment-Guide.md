# 🚀 AWS Serverless Image Compressor - Complete Deployment Guide

This guide provides a step-by-step walkthrough to deploy the Cloud-Native Image Compressor from scratch using AWS services. By the end of this guide, you will have a fully functional serverless architecture.

---

## 🛠 Prerequisites
- An active AWS Account.
- Basic understanding of AWS services (S3, IAM, Lambda, API Gateway).

---

## Step 1: Create S3 Buckets

We need three S3 buckets for this project: one for incoming images, one for processed images, and one to host the frontend web application.

1. Go to the **Amazon S3 Console**.
2. Click **Create bucket**.
3. **Create the Input Bucket:**
   - Bucket name: `image-compressor-input-yourname` (replace `yourname` to make it unique).
   - Region: Choose your preferred region (e.g., `ap-south-1`).
   - Leave the rest as default and click **Create bucket**.
4. **Create the Output Bucket:**
   - Bucket name: `image-compressor-output-yourname`.
   - Region: Same as above.
   - Leave the rest as default and click **Create bucket**.
5. **Create the Frontend Hosting Bucket:**
   - Bucket name: `image-compressor-frontend-yourname`.
   - Region: Same as above.
   - **Uncheck** "Block all public access" (acknowledge the warning).
   - Click **Create bucket**.
   - Go to the newly created frontend bucket -> **Properties** tab.
   - Scroll down to **Static website hosting**, click **Edit**, and Enable it.
   - Set the **Index document** to `index.html`. Save changes.
   - Go to the **Permissions** tab -> **Bucket policy**, click **Edit**, and paste the following policy (replace `YOUR-FRONTEND-BUCKET-NAME`):
     ```json
     {
         "Version": "2012-10-17",
         "Statement": [
             {
                 "Sid": "PublicReadGetObject",
                 "Effect": "Allow",
                 "Principal": "*",
                 "Action": "s3:GetObject",
                 "Resource": "arn:aws:s3:::YOUR-FRONTEND-BUCKET-NAME/*"
             }
         ]
     }
     ```
   - Save changes.

---

## Step 2: Set up IAM Role for Lambda

We need to give our Lambda functions permission to read from the input bucket and write to the output bucket, as well as log to CloudWatch.

1. Go to the **AWS IAM Console** -> **Roles**.
2. Click **Create role**.
3. Select **AWS service** -> **Lambda** and click **Next**.
4. Attach the following policies:
   - `AWSLambdaBasicExecutionRole` (Allows logging to CloudWatch)
   - `AmazonS3FullAccess` (Allows reading/writing to S3 buckets. *Note: In a production environment, create a custom policy restricting access only to your specific input and output buckets.*)
5. Click **Next**, name your role `ImageCompressorLambdaRole`, and click **Create role**.

---

## Step 3: Create the Image Processing Lambda Function

This function is triggered automatically when a new image is uploaded to the Input Bucket. It processes and compresses the image.

1. Go to the **AWS Lambda Console** -> **Functions**.
2. Click **Create function**.
3. **Function name:** `ImageProcessorFunction`.
4. **Runtime:** Python 3.9 (or newer).
5. **Execution role:** Select **Use an existing role** and choose the `ImageCompressorLambdaRole` created in Step 2.
6. Click **Create function**.
7. **Add the code:**
   - Under the **Code** tab, copy the contents of `lambda/Lambda code.py` from this repository and paste it into `lambda_function.py`.
   - Click **Deploy**.
8. **Add Pillow (PIL) Layer:**
   - Image processing requires the Pillow library. Scroll to the bottom of the Lambda page to the **Layers** section and click **Add a layer**.
   - You can either upload a custom Pillow zip file (via Custom layers) or specify an ARN for a public Pillow layer that matches your AWS Region and Python runtime.
   - Click **Add**.
9. **Set Environment Variables:**
   - Go to the **Configuration** tab -> **Environment variables**.
   - Click **Edit** and add:
     - Key: `OUTPUT_BUCKET`, Value: `image-compressor-output-yourname` (the output bucket name from Step 1).
   - Save.
10. **Increase Timeout and Memory:**
    - Go to **Configuration** -> **General configuration** -> **Edit**.
    - Set Memory to **512 MB** (or 256 MB at minimum).
    - Set Timeout to **1 minute**.
    - Save.
11. **Add S3 Trigger:**
    - On the function overview graph, click **Add trigger**.
    - Select **S3**.
    - Bucket: Select your Input Bucket (`image-compressor-input-yourname`).
    - Event type: `All object create events`.
    - Check the recursive invocation warning and click **Add**.

---

## Step 4: Create the API Handler Lambda Function

This function acts as the backend API to generate S3 presigned URLs for the frontend.

1. In the Lambda Console, click **Create function**.
2. **Function name:** `APIHandlerFunction`.
3. **Runtime:** Python 3.9 (or newer).
4. **Execution role:** Select the same `ImageCompressorLambdaRole`.
5. Click **Create function**.
6. **Add the code:**
   - Copy the contents of `lambda/Lambda code API.py` from this repository and paste it into `lambda_function.py`.
   - Click **Deploy**.
7. **Set Environment Variables:**
   - Go to the **Configuration** tab -> **Environment variables**.
   - Click **Edit** and add:
     - Key: `INPUT_BUCKET`, Value: `image-compressor-input-yourname`
     - Key: `OUTPUT_BUCKET`, Value: `image-compressor-output-yourname`
   - Save.

---

## Step 5: Set up API Gateway

API Gateway will expose our API Handler Lambda to the frontend.

1. Go to the **AWS API Gateway Console**.
2. Click **Create API** -> Find **HTTP API** and click **Build**.
3. **Integrations:** Click **Add integration**, select **Lambda**, and choose the `APIHandlerFunction`.
4. **API name:** `ImageCompressorAPI`. Click **Next**.
5. **Configure routes:**
   - Method: `POST`, Resource path: `/optimize`, Integration: `APIHandlerFunction`.
   - Method: `OPTIONS`, Resource path: `/optimize`, Integration: `APIHandlerFunction`.
   - Click **Next** until the API is created.
6. **Configure CORS:**
   - On the left sidebar, click **CORS**.
   - Click **Configure**.
   - Access-Control-Allow-Origins: `*` (or your frontend S3 website URL for security).
   - Access-Control-Allow-Headers: `*`
   - Access-Control-Allow-Methods: `POST`, `OPTIONS`, `GET`
   - Save.
7. **Get the Invoke URL:**
   - On the left sidebar, click **Stages**, select the `$default` stage.
   - Copy the **Invoke URL** (e.g., `https://ke3a91dqwe.execute-api.ap-south-1.amazonaws.com`).

---

## Step 6: Configure the Frontend

Now we link our frontend to the newly created backend.

1. Open `script.js` in a text editor.
2. Locate the `CONFIG` object at the top of the file.
3. Update the `API_BASE_URL` with your API Gateway Invoke URL from Step 5 (make sure there is no trailing slash).
   ```javascript
   const CONFIG = {
       API_BASE_URL: 'https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com',
       // ...
   };
   ```
4. Save the file.

---

## Step 7: Deploy the Frontend to S3

1. Go to the **Amazon S3 Console** and open your Frontend Hosting Bucket (`image-compressor-frontend-yourname`).
2. Click **Upload** and add the following files and folders from your local project:
   - `index.html`
   - `style.css`
   - `script.js`
   - `app.js` (if utilized)
   - `Screenshots/` (folder)
3. Click **Upload**.
4. Once the upload completes, go to the **Properties** tab of the bucket.
5. Scroll down to **Static website hosting** and click your **Bucket website endpoint URL**.

---

## 🎉 Step 8: Test Your Application

1. Open your S3 Website Endpoint URL in a web browser.
2. The UI should load. Check the browser console (F12) to ensure the API health check passes.
3. Upload an image using the drag-and-drop interface.
4. Verify the flow:
   - The frontend calls `/optimize` to get a presigned URL.
   - The image is uploaded directly to the S3 Input Bucket.
   - S3 triggers the ImageProcessorFunction Lambda.
   - The processed images are saved to the S3 Output Bucket.
   - The frontend displays links to download the compressed versions!

**Congratulations! Your Serverless Cloud-Native Image Compressor is now live.**
