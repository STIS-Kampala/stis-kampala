export type CongestionLabel = "low" | "medium" | "high";
export type ModelName = "gradient_boosting" | "random_forest" | "ridge";
export type RoadId =
  | "kampala_rd" | "jinja_rd" | "bombo_rd" | "masaka_rd"
  | "gaba_rd" | "portbell_rd" | "entebbe_rd" | "n_bypass";

export interface PredictRequest {
  road_id:  RoadId;
  hour:     number;
  rain_mm:  number;
  model:    ModelName;
}

export interface ConfidenceInterval {
  lower: number;
  upper: number;
}

export interface SHAPInfo {
  top_feature: string;
  value:       number;
}

export interface RiskInfo {
  accident: number;
  flood:    number;
}

export interface CostInfo {
  extra_fuel_l_per_100km: number;
  extra_co2_g:            number;
}

export interface PredictResponse {
  road_id:       string;
  road_name:     string;
  label:         CongestionLabel;
  confidence:    number;
  delay_ratio:   number;
  ci_95:         ConfidenceInterval;
  travel_min:    number;
  base_min:      number;
  shap:          SHAPInfo;
  risk:          RiskInfo;
  cost:          CostInfo;
  model_used:    ModelName;
  model_version: string;
  latency_ms:    number;
}

export interface RoadMeta {
  id:       RoadId;
  name:     string;
  type:     string;
  base_min: number;
  km:       number;
  has_boda: boolean;
  label:    CongestionLabel;
}

export interface ModelMetrics {
  mae:      number;
  rmse:     number;
  r2:       number;
  accuracy: number;
  f1:       number;
  cv_mae:   number;
  cv_std:   number;
}

export interface ModelInfo {
  name:     ModelName;
  label:    string;
  version:  string;
  metrics:  ModelMetrics;
  is_best:  boolean;
}
