terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.6.0"
    }
  }
}

provider "google" {
  # This points to the service account key you will download from GCP
  credentials = file("./keys/gcp-service-account.json")
  project     = var.project_id
  region      = var.region
}

# The Cloud Data Lake (Bronze Layer)
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${var.project_id}-agri-lake"
  location      = var.region
  force_destroy = true 
  
  # Rule 1: Clean up development data after 30 days to avoid accumulating costs
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  # Rule 2: Clean up failed pipeline uploads instantly (Cost-saving best practice)
  lifecycle_rule {
    condition {
      age = 1 
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

# The Cloud Data Warehouse (Silver/Gold Layers)
resource "google_bigquery_dataset" "production_dataset" {
  dataset_id                  = "agri_climate_warehouse"
  location                    = var.region
  description                 = "Warehouse for Farm Yield and Weather Data"
  delete_contents_on_destroy  = true
}