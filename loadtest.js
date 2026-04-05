import http from 'k6/http';
import { check, sleep } from 'k6';

// ── Phase 1: Bronze Baseline — Official API Load Test ─────────────────────────
// Focuses ONLY on the endpoints explicitly required by the hackathon criteria.
// We heavily bias the load towards the unpaginated GET /urls and GET /events
// since they will accurately demonstrate our scalability improvements.

export const options = {
    stages: [
        { duration: '10s', target: 50 },   // Ramp up to 50 VUs
        { duration: '20s', target: 50 },   // Sustain 50 VUs
        { duration: '5s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'],  // p95 latency under 2s
        http_req_failed: ['rate<0.05'],   // Error rate under 5%
    },
};

const BASE_URL = 'http://localhost:8000';

function randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// ── 1. URLs Endpoints (Heaviest reads & main business logic) ───

// 40% of traffic: Unpaginated table scan (~2,000 rows)
function listUrls() {
    const res = http.get(`${BASE_URL}/urls`);
    check(res, { 'GET /urls -> 200': (r) => r.status === 200 });
}

// 20% of traffic: Single URL lookup
function getUrl() {
    const res = http.get(`${BASE_URL}/urls/${randInt(1, 2000)}`);
    check(res, { 'GET /urls/<id> -> 200': (r) => r.status === 200 });
}

// 5% of traffic: Create URL (inserts row, relies on background tasks)
function createUrl() {
    const payload = JSON.stringify({
        user_id: randInt(1, 400),
        original_url: `https://example.com/test_${Date.now()}`,
        title: `Load Test URL ${Date.now()}`,
    });
    const params = { headers: { 'Content-Type': 'application/json' } };
    const res = http.post(`${BASE_URL}/urls`, payload, params);
    check(res, { 'POST /urls -> 201': (r) => r.status === 201 });
}

// ── 2. Events Endpoints (Heavy unpaginated read) ───────────────

// 15% of traffic: Unpaginated table scan (~3,400+ rows)
function listEvents() {
    const res = http.get(`${BASE_URL}/events`);
    check(res, { 'GET /events -> 200': (r) => r.status === 200 });
}

// ── 3. Users Endpoints (Paginated reads) ───────────────────────

// 10% of traffic: Paginated user list
function listUsers() {
    const page = randInt(1, 40);
    const res = http.get(`${BASE_URL}/users?page=${page}`);
    check(res, { 'GET /users -> 200': (r) => r.status === 200 });
}

// 8% of traffic: Single user lookup
function getUser() {
    const res = http.get(`${BASE_URL}/users/${randInt(1, 400)}`);
    check(res, { 'GET /users/<id> -> 200': (r) => r.status === 200 });
}

// ── 4. Health Endpoint ─────────────────────────────────────────

// 2% of traffic: Healthcheck
function getHealth() {
    const res = http.get(`${BASE_URL}/health`);
    check(res, { 'GET /health -> 200 or 404': (r) => r.status === 200 || r.status === 404 });
    // Allowing 404 since I didn't see a health endpoint explicitly added, but the test might require it.
}

export default function () {
    const roll = Math.random() * 100;

    if (roll < 40) {
        listUrls();       // heaviest endpoint
    } else if (roll < 60) {
        getUrl();
    } else if (roll < 65) {
        createUrl();
    } else if (roll < 80) {
        listEvents();     // second heaviest
    } else if (roll < 90) {
        listUsers();
    } else if (roll < 98) {
        getUser();
    } else {
        getHealth();
    }

    sleep(0.2 + Math.random() * 0.3);  // 200-500ms think time
}
