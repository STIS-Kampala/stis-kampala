import type {
  PredictRequest,
  PredictResponse,
  RoadMeta,
  ModelInfo,
} from "../types/api";

const BASE = "https://meticulous-embrace-production-8241.up.railway.app";
const API_KEY = "stis-kampala-2026-secret";

class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API ${status}: ${detail}`);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...(options?.headers),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  predict(req: PredictRequest): Promise<PredictResponse> {
    return request<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },
  predictNow(road_id: string, rain_mm = 0): Promise<PredictResponse> {
    return request<PredictResponse>(`/predict/now/${road_id}?rain_mm=${rain_mm}`);
  },
  roads(): Promise<RoadMeta[]> {
    return request<RoadMeta[]>("/roads");
  },
  models(): Promise<ModelInfo[]> {
    return request<ModelInfo[]>("/models");
  },
  weather(): Promise<{ temperature: number; humidity: number; rainfall: number }> {
    return request("/weather/current");
  },
};

export { ApiError };
