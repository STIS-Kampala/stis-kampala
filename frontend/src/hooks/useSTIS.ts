import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { PredictRequest, PredictResponse } from "../types/api";

export const QK = {
  roads:   ["roads"]   as const,
  models:  ["models"]  as const,
  weather: ["weather"] as const,
};

export function useRoads() {
  return useQuery({ queryKey: QK.roads,  queryFn: api.roads,   staleTime: Infinity });
}
export function useModels() {
  return useQuery({ queryKey: QK.models, queryFn: api.models,  staleTime: Infinity });
}
export function useWeather() {
  return useQuery({ queryKey: QK.weather, queryFn: api.weather, refetchInterval: 300000 });
}
export function usePredict() {
  return useMutation({ mutationFn: api.predict });
}
export function usePredictionHistory() {
  const qc = useQueryClient();
  const history: PredictResponse[] = qc.getQueryData(["predictionHistory"]) ?? [];
  function push(result: PredictResponse) {
    qc.setQueryData(["predictionHistory"], [result, ...history].slice(0, 8));
  }
  function clear() {
    qc.setQueryData(["predictionHistory"], []);
  }
  return { history, push, clear };
}
