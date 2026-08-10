import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const keys = (process.env.GROQ_KEYS ?? "").split(",").map((item) => item.trim()).filter(Boolean);
    if (!keys.length) return NextResponse.json({ error: "GROQ_KEYS is not configured." }, { status: 503 });

    const summary = {
      products: Number(body.products ?? 0),
      averageScore: Number(body.averageScore ?? 0).toFixed(1),
      topBrand: String(body.topBrand ?? "Unknown").slice(0, 80),
      averagePrice: Number(body.averagePrice ?? 0).toFixed(2),
      inStock: Number(body.inStock ?? 0),
    };
    const requestBody = JSON.stringify({
      model: "llama-3.1-8b-instant",
      temperature: 0.25,
      max_tokens: 700,
      messages: [
        { role: "system", content: "You are a luxury footwear market analyst. Return a concise executive report with observations, risks, and three concrete actions. Use Markdown." },
        { role: "user", content: `Analyze this filtered catalog: ${JSON.stringify(summary)}` },
      ],
    });

    let lastStatus = 500;
    for (const key of keys) {
      const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
        body: requestBody,
      });
      lastStatus = response.status;
      if (!response.ok) continue;
      const result = await response.json();
      return NextResponse.json({ insight: result.choices?.[0]?.message?.content ?? "No insight returned." });
    }
    const project = process.env.GCP_PROJECT_ID;
    const region = process.env.GCP_REGION ?? "us-central1";
    if (!project) throw new Error(`All Groq keys failed; last status ${lastStatus}`);

    const tokenResponse = await fetch("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token", {
      headers: { "Metadata-Flavor": "Google" },
    });
    if (!tokenResponse.ok) throw new Error(`Vertex identity failed (${tokenResponse.status})`);
    const { access_token: accessToken } = await tokenResponse.json();
    const vertexResponse = await fetch(
      `https://${region}-aiplatform.googleapis.com/v1/projects/${project}/locations/${region}/publishers/google/models/gemini-2.5-flash:generateContent`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: "You are a luxury footwear market analyst. Return a concise executive report with observations, risks, and three concrete actions. Use Markdown." }] },
          contents: [{ role: "user", parts: [{ text: `Analyze this filtered catalog: ${JSON.stringify(summary)}` }] }],
          generationConfig: { temperature: 0.25, maxOutputTokens: 700 },
        }),
      },
    );
    if (!vertexResponse.ok) throw new Error(`Vertex AI request failed (${vertexResponse.status})`);
    const vertexResult = await vertexResponse.json();
    const insight = vertexResult.candidates?.[0]?.content?.parts?.map((part: { text?: string }) => part.text ?? "").join("") ?? "No insight returned.";
    return NextResponse.json({ insight });
  } catch (error) {
    console.error("Insight API error", error);
    return NextResponse.json({ error: "The AI report could not be generated." }, { status: 500 });
  }
}
