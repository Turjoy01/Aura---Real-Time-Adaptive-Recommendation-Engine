# Deployment Guide

## MongoDB Setup

### Local Development
\`\`\`bash
mongod  # Start MongoDB locally
\`\`\`

### MongoDB Atlas (Cloud)
1. Create cluster at https://www.mongodb.com/cloud/atlas
2. Get connection string
3. Set `MONGODB_URL` in `.env`

### Create Indexes
\`\`\`javascript
// In MongoDB shell or Atlas UI:
db.user_behavior_events.createIndex({ "user_id": 1, "timestamp": -1 })
db.user_behavior_events.createIndex({ "session_id": 1 })
db.user_preference_profile.createIndex({ "user_id": 1 })
db.events.createIndex({ "location": "2dsphere" })  // For geospatial queries
\`\`\`

---

## Running the Service

### Development
\`\`\`bash
uvicorn src.main:app --reload --port 8000
\`\`\`

### Production
\`\`\`bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 src.main:app
\`\`\`

---

## Environment Variables

Create `.env` file:
\`\`\`
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/ventyy
OPENAI_API_KEY=sk-proj-...
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
ENVIRONMENT=production
DEBUG=False
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
\`\`\`

---

## Docker Deployment

### Build
\`\`\`bash
docker build -t ventyy-recommendation:1.0.0 .
\`\`\`

### Run
\`\`\`bash
docker run -p 8000:8000 \
  -e MONGODB_URL="mongodb+srv://..." \
  -e OPENAI_API_KEY="sk-proj-..." \
  -e SECRET_KEY="your-secret" \
  ventyy-recommendation:1.0.0
\`\`\`

---

## Kubernetes Deployment

\`\`\`yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ventyy-recommendation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ventyy-recommendation
  template:
    metadata:
      labels:
        app: ventyy-recommendation
    spec:
      containers:
      - name: recommendation-service
        image: ventyy-recommendation:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: ventyy-secrets
              key: mongodb-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ventyy-secrets
              key: openai-api-key
        livenessProbe:
          httpGet:
            path: /v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
\`\`\`

---

## Monitoring

### Health Check
\`\`\`bash
curl http://localhost:8000/v1/health
\`\`\`

### Logs
\`\`\`bash
docker logs -f <container-id>
\`\`\`

### Metrics (Future)
- Response times
- Error rates
- Recommendation diversity
- User engagement
