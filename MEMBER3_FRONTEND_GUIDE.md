# Member 3 Frontend Implementation Guide

## What You Should Build and Show

Your responsibility is the complete website and demo layer. The frontend should prove that the AWS backend is useful, secure, and easy to understand.

## Pages Implemented

1. Login
   - Demo login for presentation practice.
   - Cognito hosted UI login when AWS values are added in `.env`.

2. Dashboard
   - Secure file count.
   - Verified access count.
   - Blocked suspicious attempts.
   - Expiring files.
   - Recent protected files.
   - Recent security events.

3. Upload
   - File picker.
   - Classification: Internal, Confidential, Restricted.
   - Expiry window.
   - Allowed IP policy.
   - MFA requirement.
   - Upload progress.
   - Designed to call Lambda/API Gateway, then upload using S3 pre-signed URL.

4. Access Verification
   - Select file.
   - Enter source IP.
   - Select trusted/untrusted device.
   - Simulate expired access.
   - Show ALLOW/DENY decision.
   - Show token, expiry, IP, device, and DynamoDB policy checks.
   - Generate temporary secure URL only after allowed access.
   - Delete file to show lifecycle enforcement.

5. Logs and Alerts
   - CloudWatch-style logs.
   - CloudTrail audit-style events.
   - GuardDuty suspicious access event.
   - SNS test alert button.

6. AWS Flow
   - Visual architecture flow.
   - Service coverage for all required AWS services.

## Backend API Contract for Member 2

Ask Member 2 to expose these API Gateway endpoints:

```txt
POST   /upload
POST   /verify
GET    /access?fileId=<id>
DELETE /delete/<fileId>
GET    /logs
GET    /dashboard
POST   /alerts/test
```

## Environment Setup

Create `.env`:

```txt
VITE_API_BASE_URL=https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod
VITE_AWS_REGION=ap-south-1
VITE_COGNITO_DOMAIN=https://your-domain.auth.ap-south-1.amazoncognito.com
VITE_COGNITO_CLIENT_ID=your-cognito-app-client-id
VITE_COGNITO_REDIRECT_URI=http://localhost:5173
VITE_DEMO_MODE=false
```

Use `VITE_DEMO_MODE=true` until the backend is ready.

## Demo Script

1. Open website and login.
2. Show dashboard metrics and AWS services.
3. Upload a sample file with `Restricted` classification and short expiry.
4. Explain that the file goes to S3 with KMS encryption and metadata goes to DynamoDB.
5. Go to Access page and verify with trusted IP/device.
6. Show ALLOW decision and generate temporary URL.
7. Change source IP to `203.0.113.25` or device to `Untrusted`.
8. Show DENY decision and explain Zero Trust continuous verification.
9. Open Logs page and show CloudWatch, CloudTrail, GuardDuty, SNS.
10. Trigger test SNS alert.
11. Delete file or simulate expired access to show lifecycle enforcement.

## Presentation Points

- The frontend is not only a file uploader; it is a security operations interface.
- Every access request is verified, even after login.
- Files are time-bound using expiry metadata and EventBridge automation.
- Suspicious access is blocked and logged.
- AWS services are serverless, scalable, monitored, and auditable.

