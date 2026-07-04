variable "project_id" {
    description = "The GCP Project ID"
    type        = string
}

variable "region" {
    description = "The GCP region for services"
    type        = string
    default     = "us-central1"
}

variable "app_name" {
    description = "Base name for all resources"
    type        = string
    default     = "enterprise-rag"
}

variable "qdrant_url" {
    description = "Qdrant Cloud endpoint"
    type        = string
}

variable "qdrant_api_key" {
    description = "Qdrant Cloud API Key"
    type        = string
    sensitive   = true
}

variable "groq_api_key" {
    description = "Groq API Key"
    type        = string
    sensitive   = true
}

variable "groq_fallback_api_key" {
    description = "Fallback Groq API Key"
    type        = string
    sensitive   = true
    default     = ""
}

variable "portkey_api_key" {
    description = "Portkey API Key for gateway routing"
    type        = string
    sensitive   = true
    default     = ""
}

variable "portkey_config_id" {
    description = "Portkey config ID used by the LLM gateway"
    type        = string
    default     = ""
}

variable "nvidia_api_key" {
    description = "NVIDIA API Key for guardrails"
    type        = string
    sensitive   = true
    default     = ""
}

variable "judge_groq" {
    description = "Groq model name used by the evals judge"
    type        = string
    default     = "llama-3.3-70b-versatile"
}

variable "db_password" {
    description = "Postgres Password"
    type        = string
    sensitive   = true
}

variable "logfire_token" {
    description = "Logfire Write Token"
    type        = string
    sensitive   = true
}

variable "langsmith_api_key" {
    type      = string
    sensitive = true
}

variable "langsmith_project" {
    type    = string
    default = "rag_scale_test"
}

variable "doc_ai_processor_id" {
    description = "The Google Cloud Document AI Processor ID"
    type        = string
}