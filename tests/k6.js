import http from 'k6/http';
import { check, sleep } from 'k6';
import { SharedArray } from 'k6/data';

// Load questions from the file
const questions = new SharedArray('questions', function () {
    return open('questions.txt').split('\n').filter(q => q.trim() !== '');
});

export let options = {
    stages: [
        { duration: '1m', target: 10 }, // Ramp-up to 10 RPS over 1 minute
        { duration: '5m', target: 50 }, // Stay at 10 RPS for 5 minutes
        { duration: '1m', target: 0 },  // Ramp-down to 0 RPS
    ],
};
export default function () {
    const url = 'http://84.201.168.132:8080/api/answers'; // Replace with your actual endpoint
    // Pick a random question from the list
    const question = questions[Math.floor(Math.random() * questions.length)];

    const payload = JSON.stringify({
        question: question,
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const res = http.post(url, payload, params);

    check(res, {
        'status was 200': (r) => r.status === 200,
        'response contains answer': (r) => JSON.parse(r.body).answer !== '',
        'response contains class_1': (r) => JSON.parse(r.body).class_1 !== '',
        'response contains class_2': (r) => JSON.parse(r.body).class_2 !== '',
    });

    sleep(1); // Sleep for 1 second to simulate pacing for 1 RPS per virtual user
}
