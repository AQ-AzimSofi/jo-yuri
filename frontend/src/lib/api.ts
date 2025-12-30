const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8421";

export interface SearchResult {
  id: string;
  filename: string;
  score: number;
  url: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

export interface VerifyResponse {
  is_joyuri: boolean;
  confidence: number;
  faces_detected: number;
  message: string;
}

export interface ImageItem {
  id: string;
  payload: {
    filename: string;
    path: string;
  };
}

export async function searchImages(query: string, limit = 12): Promise<SearchResponse> {
  const res = await fetch(`${API_URL}/api/search/?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function verifyImage(file: File): Promise<VerifyResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/api/verify/`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Verification failed");
  return res.json();
}

export async function listImages(): Promise<ImageItem[]> {
  const res = await fetch(`${API_URL}/api/images/`);
  if (!res.ok) throw new Error("Failed to list images");
  return res.json();
}

export function getImageUrl(filename: string): string {
  return `${API_URL}/api/images/file/${filename}`;
}
