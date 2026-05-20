# Cloud-Native Zero Trust Secure Data Exchange Frontend

React frontend for a Zero Trust secure file exchange platform using AWS services:
S3, Lambda, API Gateway, Cognito, DynamoDB, EventBridge, CloudWatch, CloudTrail, GuardDuty, SNS, KMS, and IAM.

## Run Locally

```bash
npm install
npm run dev
```

Open the local Vite URL. The app starts in demo mode by default.

## Connect Real AWS Backend

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Update:

- `VITE_API_BASE_URL`: API Gateway stage URL
- `VITE_AWS_REGION`: AWS region
- `VITE_COGNITO_DOMAIN`: Cognito hosted UI domain
- `VITE_COGNITO_CLIENT_ID`: Cognito app client ID
- `VITE_COGNITO_REDIRECT_URI`: local or deployed frontend URL
- `VITE_DEMO_MODE=false`: use real APIs

Expected backend endpoints:

- `POST /upload`
- `POST /verify`
- `GET /access?fileId=...`
- `DELETE /delete/{fileId}`
- `GET /logs`
- `GET /dashboard`
- `POST /alerts/test`

Every request sends `Authorization: Bearer <token>` when a Cognito token exists.

## Demo Scenarios

1. Login as demo user.
2. Upload a file with expiry and access policy.
3. Verify authorized access.
4. Trigger blocked access by changing IP/device inputs.
5. Show CloudWatch-style logs and GuardDuty/SNS alerts.
6. Delete or expire a file to show lifecycle enforcement.

# Cloud-computing
