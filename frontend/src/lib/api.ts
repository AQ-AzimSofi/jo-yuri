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

export interface ModelInfo {
  id: string;
  name: string;
  family: string;
  vector_dim: number;
  description: string;
  is_loaded: boolean;
  is_indexed: boolean;
  indexed_count: number;
}

export interface CurrentModel {
  model_id: string;
  name: string;
  is_loaded: boolean;
  is_indexed: boolean;
  indexed_count: number;
}

export interface LoadProgress {
  status: "starting" | "complete" | "error";
  progress?: number;
  error?: string;
}

export interface IndexProgress {
  status: "loading_model" | "starting" | "indexing" | "file_error" | "complete" | "error";
  current?: number;
  total?: number;
  file?: string;
  error?: string;
}

export async function searchImages(
  query: string,
  limit = 12,
  modelId?: string
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    limit: limit.toString(),
  });
  if (modelId) params.set("model", modelId);

  const res = await fetch(`${API_URL}/api/search/?${params}`);
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

export async function listModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_URL}/api/models/`);
  if (!res.ok) throw new Error("Failed to list models");
  return res.json();
}

export async function getCurrentModel(): Promise<CurrentModel> {
  const res = await fetch(`${API_URL}/api/models/current`);
  if (!res.ok) throw new Error("Failed to get current model");
  return res.json();
}

export async function setCurrentModel(modelId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/models/current`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_id: modelId }),
  });
  if (!res.ok) throw new Error("Failed to set model");
}

export function loadModelStream(
  modelId: string,
  onProgress: (data: LoadProgress) => void
): EventSource {
  const es = new EventSource(`${API_URL}/api/models/load/${encodeURIComponent(modelId)}/stream`);
  es.onmessage = (e) => onProgress(JSON.parse(e.data));
  es.onerror = () => es.close();
  return es;
}

export function indexModelStream(
  modelId: string,
  onProgress: (data: IndexProgress) => void
): EventSource {
  const es = new EventSource(`${API_URL}/api/models/index/${encodeURIComponent(modelId)}/stream`);
  es.onmessage = (e) => onProgress(JSON.parse(e.data));
  es.onerror = () => es.close();
  return es;
}
