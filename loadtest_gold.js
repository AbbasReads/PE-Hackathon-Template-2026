import http from 'k6/http';
import { check, sleep } from 'k6';

// ── Phase 3: Gold — 500+ Concurrent User Tsunami ──────────────────────────────
// Tests Redis caching + horizontal scaling under extreme concurrent load.

export const options = {
    stages: [
        { duration: '10s', target: 600 },  // Ramp up to 600 VUs
        { duration: '20s', target: 600 },  // Sustain 600 VUs
        { duration: '5s', target: 0 },     // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<3000'],  // p95 latency under 3s
        http_req_failed: ['rate<0.05'],     // Error rate under 5%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const USER_COUNT = 400;

function randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function setup() {
    for (let i = 1; i <= USER_COUNT; i++) {
        http.post(
            `${BASE_URL}/users`,
            JSON.stringify({
                username: `k6-user-${i}`,
                email: `k6-user-${i}@example.com`,
            }),
            { headers: { 'Content-Type': 'application/json' } },
        );
    }

    for (let i = 1; i <= 100; i++) {
        http.post(
            `${BASE_URL}/urls`,
            JSON.stringify({
                user_id: randInt(1, USER_COUNT),
                original_url: `https://example.com/seed-${i}`,
                title: `Seed URL ${i}`,
            }),
            { headers: { 'Content-Type': 'application/json' } },
        );
    }
}

// ── 1. URLs Endpoints (Heaviest reads & main business logic) ───

// 40% of traffic: Paginated URL list (cached in Redis)
function listUrls() {
    const res = http.get(`${BASE_URL}/urls`);
    check(res, { 'GET /urls -> 200': (r) => r.status === 200 });
}

// 20% of traffic: Single URL lookup (cached in Redis)
function getUrl() {
    const res = http.get(`${BASE_URL}/urls/${randInt(1, 100)}`);
    check(res, { 'GET /urls/<id> -> 200 or 404': (r) => r.status === 200 || r.status === 404 });
}

// 5% of traffic: Create URL
function createUrl() {
    const payload = JSON.stringify({
        user_id: randInt(1, USER_COUNT),
        original_url: `https://example.com/test_${Date.now()}`,
        title: `Load Test URL ${Date.now()}`,
    });
    const params = { headers: { 'Content-Type': 'application/json' } };
    const res = http.post(`${BASE_URL}/urls`, payload, params);
    check(res, { 'POST /urls -> 201': (r) => r.status === 201 });
}

// ── 2. Events Endpoints (Cached heavy read) ────────────────────

// 15% of traffic: Event log list (cached in Redis)
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
    const res = http.get(`${BASE_URL}/users/${randInt(1, USER_COUNT)}`);
    check(res, { 'GET /users/<id> -> 200': (r) => r.status === 200 });
}

// ── 4. Health Endpoint ─────────────────────────────────────────

// 2% of traffic: Healthcheck
function getHealth() {
    const res = http.get(`${BASE_URL}/health`);
    check(res, { 'GET /health -> 200': (r) => r.status === 200 });
}

export default function () {
    const roll = Math.random() * 100;

    if (roll < 40) {
        listUrls();       // heaviest endpoint (cached)
    } else if (roll < 60) {
        getUrl();          // single lookup (cached)
    } else if (roll < 65) {
        createUrl();
    } else if (roll < 80) {
        listEvents();     // second heaviest (cached)
    } else if (roll < 90) {
        listUsers();
    } else if (roll < 98) {
        getUser();
    } else {
        getHealth();
    }

    sleep(0.2 + Math.random() * 0.3);  // 200-500ms think time
}
