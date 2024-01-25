export async function POST(
    request: Request,
) {
    const body = await request.json()
    if (body.type === 'simple' || 'reranked') {
        const response = await fetch(`http://127.0.0.1:8000/api/resume/${body.type}`, {
            method: 'POST',
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({
                job_description: body.jobDescription,
                top_k: body.topK
            })
        });
        const responseBody = await response.json();

        return new Response(JSON.stringify(responseBody.hits), {
            headers: {"Content-Type": "application/json"},
            status: 200,
        });
    }
}