import { openai } from '@ai-sdk/openai';
import { convertToModelMessages, streamText, UIMessage } from "ai"

export async function POST(req: Request) {    
    // Use AI SDK directly to with LLMs
    // const { messages }: { messages: UIMessage[] } = await req.json()
    // const result = streamText({
        // model: openai('gpt-4o'),
        // messages: convertToModelMessages(messages)
    // })
    // return result.toUIMessageStreamResponse();

    const body = await req.text();
    const upstream = await fetch(process.env.FASTAPI_URL + "/chat", {
        method: "POST",
        headers: {
            "content-type": "application/json",
        },
        body,
    })
    
    console.log(upstream);
    

    const headers = new Headers(upstream.headers);
    headers.set("content-type", "text/event-stream");
    headers.set("x-vercel-ai-ui-message-stream", "v1"); // for use with AI SDK
    headers.set("cache-control", "no-store");

    return new Response(upstream.body, { status: upstream.status, headers});
}