# Aura – Real-Time Adaptive Recommendation Engine

**Intelligent, Reinforcement-Learning-Powered Personalization**

Aura is a high-performance microservice designed to deliver sub-300ms personalized recommendations. Powered by Multi-Armed Bandits and LLM-driven query parsing, it adapts instantly to user behavior—no batch jobs required. Every click, view, and interaction refines the user's profile in real-time, transforming cold-start users into engaged VIPs within minutes.

---

## 🚀 Key Capabilities
- **Real-Time Learning**: Instantly adjusts preferences based on live interactions.
- **Adaptive Exploration**: Balances personalization (85%) with discovery (15%) using bandit algorithms.
- **Natural Language Search**: "Techno in Brooklyn tonight under $40" → structured, relevant results.
- **Cold-Start Logic**: Smart blending of trends, demographics, and intent for new users.

---

## 📋 Installation

### Prerequisites
- Python 3.11+
- MongoDB (local or Atlas)
- OpenAI API key

### Setup

1. **Clone and install**
\`\`\`bash
git clone <repo>
cd ventyy-recommendation
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
\`\`\`

2. **Configure environment**
\`\`\`bash
cp .env.example .env
# Edit .env with your MongoDB URL and OpenAI API key
\`\`\`

3. **Generate a Test Token**
   Since this service relies on a separate Auth Service, you must generate a dev token manually:
   ```bash
   python generate_token.py <your_user_id>
   # Example: python generate_token.py user123
   ```
   Copy the output token.

4. **Run the service**
   ```bash
   uvicorn src.main:app --reload
   ```

   Service will be available at `http://localhost:8000`

---

## 🔥 Swagger UI – Interactive Testing

**Visit:** http://localhost:8000/docs

All endpoints are documented with:
- Clear descriptions and use cases
- Example requests and responses
- Real-time error handling
- JWT authentication testing


### Quick Start in Swagger:
1. Open the UI.
2. No authentication required.
3. Test endpoints directly.

---

## 🛣️ API Endpoints (Logical Flow)

### 1. Health Check
*Verify system status*
```
GET /v1/health
```

### 2. User Onboarding
*Start here first*
```
POST /v1/user/onboarding
```

### 3. Discovery (Recommendations)
*Get personalized events*
```
POST /v1/recommend/feed
```
Get 30 personalized events for home tab

```
POST /v1/recommend/natural
```
Search with natural language: "techno in Brooklyn tonight under $40"

```
POST /v1/recommend/highlights
```
Get 5-10 trending events for Highlights row

### 4. Interaction
*Log user actions to improve personalization*
```
POST /v1/behavior/log
```
Log every user action (search, view, like, purchase, skip, etc.)

### Feedback & Learning
```
POST /v1/feedback/reward
```
Submit reinforcement learning feedback (purchase, skip, like)

### 5. Debugging & Tools
```
POST /v1/user/reset
```
**[NEW]** Reset your profile (delete preferences) to restart the cold-start phase.

```
GET /v1/user/profile
```
View your current preference profile

---

## 📊 User Preference Profile

Each user has a MongoDB document tracking:

\`\`\`json
{
  "user_id": "ObjectId",
  "onboarding_intent": "explore | create | freelance",
  "age": 24,
  "gender": "male | female | non_binary",
  "preferred_categories": [
    {"name": "Techno", "score": 0.97},
    {"name": "Hip-Hop", "score": 0.81}
  ],
  "preferred_price_range": {
    "avg": 28,
    "sweet_spot_min": 15,
    "sweet_spot_max": 45
  },
  "preferred_locations": [
    {"city": "Brooklyn", "neighborhood": "Williamsburg", "score": 0.94}
  ],
  "total_events_attended": 18,
  "cold_start_completed": true
}
\`\`\`

---

## 🤖 Reinforcement Learning Flow

Every `/feedback/reward` call:

1. ✓ Updates raw behavior event with reward value
2. ✓ Instantly adjusts preference scores (+0.15 for purchase, -0.05 for skip)
3. ✓ Invalidates user cache
4. ✓ Next recommendation call uses brand-new profile

**No nightly batch jobs. Pure real-time learning.**

---

## ❄️ Cold-Start Logic

For users with < 3 behavior events, blend 4 signals:

1. **Popular in area** (40%) – trending events nearby
2. **Trending by age group** (25%) – events liked by similar users
3. **Intent-matched** (20%) – explore/create/freelance alignment
4. **Time patterns** (15%) – events happening right now

---

## 🧠 Natural Language Parsing

Uses OpenAI to extract structured intent:

\`\`\`
Input:  "best hip hop in bushwick tonight under $40"
Output: {
  "categories": ["Hip-Hop"],
  "price_max": 40,
  "time_slot": "Late Night",
  "location": "Bushwick",
  "vibe_keywords": ["energetic", "underground"]
}
\`\`\`

---

## 📁 Project Structure

\`\`\`
src/
├── main.py                          # FastAPI app entry point
├── core/
│   ├── config.py                   # Settings & environment
│   └── security.py                 # JWT verification
├── db/
│   └── mongodb.py                  # MongoDB connection
├── models/
│   ├── behavior.py                 # Behavior events
│   ├── preference.py               # User preferences
│   └── recommend.py                # Recommendation responses
├── services/
│   ├── preference_updater.py       # Real-time preference scoring
│   ├── cold_start.py               # Cold-start engine
│   ├── natural_parser.py           # LLM query parsing
│   └── bandit.py                   # Multi-armed bandit
├── routers/
│   ├── behavior.py                 # /v1/behavior/* endpoints
│   ├── recommend.py                # /v1/recommend/* endpoints
│   └── user.py                     # /v1/user/* endpoints
└── utils/
    └── __init__.py
\`\`\`

---

## 🔐 Authentication
**DISABLED** for local development.

All endpoints are open and do not require headers.


---

## 🚀 Deployment

### Docker (Recommended)

\`\`\`dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
\`\`\`

### Vercel / Lambda / Cloud Run

Set environment variables:
- `MONGODB_URL`
- `OPENAI_API_KEY`
- `SECRET_KEY`

---

## 📈 Performance Targets

- **Response Time**: < 300ms at 100K DAU
- **Throughput**: 1000+ req/sec per instance
- **Availability**: 99.9% uptime
- **Learning Speed**: Real-time profile updates

---

## 🛠️ Testing with Swagger

1. **Health check**: GET `/v1/health`
2. **Onboard user**: POST `/v1/user/onboarding` with intent/age/gender
3. **Log behavior**: POST `/v1/behavior/log` with event data
4. **Get recommendations**: POST `/v1/recommend/feed` with lat/lng
5. **Submit reward**: POST `/v1/feedback/reward` with event_id and reward value
6. **View profile**: GET `/v1/user/profile` to see learned preferences

---

## 📝 License

Proprietary – Ventyy Inc.

---

## 🤝 Support

For issues or questions, contact the recommendation team.

<img width="1102" height="922" alt="image" src="https://github.com/user-attachments/assets/e24ed16e-10d6-43d7-9f9b-1d7e69c5ecae" />

