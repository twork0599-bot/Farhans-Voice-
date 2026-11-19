import { FishAudioClient } from "fish-audio";

export const runtime = "nodejs";
export const maxDuration = 60;

const recent = new Map();

export async function POST(request) {
  try {
    const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
    const now = Date.now();
    const hits = (recent.get(ip) || []).filter((time) => now - time < 60_000);
    if (hits.length >= 8) {
      return Response.json({ error: "Too many requests. Please wait one minute." }, { status: 429 });
    }
    hits.push(now);
    recent.set(ip, hits);

    const apiKey = process.env.FISH_API_KEY;
    if (!apiKey) return Response.json({ error: "Fish Audio API key is not configured on the server." }, { status: 503 });

    const body = await request.json();
    const text = typeof body.text === "string" ? body.text.trim() : "";
    const referenceId = typeof body.referenceId === "string" ? body.referenceId.trim() : "";
    const model = ["s2.1-pro", "s2-pro", "s2.1-pro-free"].includes(body.model) ? body.model : "s2.1-pro";
    const speed = Number(body.speed ?? 1);

    if (!text) return Response.json({ error: "Please enter text to generate." }, { status: 400 });
    if (text.length > 5000) return Response.json({ error: "Text limit is 5,000 characters." }, { status: 400 });
    if (!referenceId || referenceId.length > 200) return Response.json({ error: "Enter a valid Voice ID." }, { status: 400 });
    if (!Number.isFinite(speed) || speed < 0.5 || speed > 2) return Response.json({ error: "Speed must be between 0.5x and 2.0x." }, { status: 400 });

    const client = new FishAudioClient({ apiKey });
    const audio = await client.textToSpeech.convert({
      text,
      reference_id: referenceId,
      format: "mp3",
      mp3_bitrate: 128,
      latency: "normal",
      prosody: { speed },
    }, model);

    return new Response(audio, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Disposition": 'inline; filename="farhan-voice.mp3"',
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    console.error("Fish Audio TTS error:", error);
    const message = error?.status === 401 ? "Fish Audio rejected the API key. Check the server environment variable." :
      error?.status === 402 ? "Fish Audio account has insufficient credits for this model." :
      "Audio generation failed. Check the Voice ID, model and Fish Audio account.";
    return Response.json({ error: message }, { status: 502 });
  }
}
