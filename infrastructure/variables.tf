variable "project_id" {
  description = "Your GCP Project ID"
  default     = "kestra-sandbox-504410" # Change this to your actual GCP Project ID
}

variable "region" {
  description = "Region for GCP resources"
  default     = "us-central1"
}