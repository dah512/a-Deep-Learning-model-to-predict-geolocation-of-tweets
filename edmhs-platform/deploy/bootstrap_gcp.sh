#!/usr/bin/env bash
# One-time setup of the EDMHS.org Google Cloud / Firebase project. Run on your own computer,
# signed in with `gcloud auth login` as an account that can create projects and link billing.
#
#   GITHUB_REPO=<org>/edmhs-org BILLING_ACCOUNT=XXXXXX-XXXXXX-XXXXXX ./deploy/bootstrap_gcp.sh
#
# Safe to re-run: each create step skips what already exists.
# What it creates (project edmhs-org, region us-central1):
#   - APIs, Artifact Registry repo "edmhs"
#   - Cloud SQL Postgres 16 instance "edmhs-pg" (private to the project, backups on), db "edmhs"
#   - Schema from db/init/001 + 002 (NOT db/dev synthetic data), login roles ict_api / ana_api
#   - Secret Manager secrets: INTAKE_DATABASE_URL, ANALYTICS_DATABASE_URL, PII_KEY
#   - Runtime service account for Cloud Run; deployer service account for GitHub Actions
#   - Workload Identity Federation so GitHub Actions deploys without a stored key
#   - Firebase on the project + Hosting site "edmhs-org"
set -euo pipefail

PROJECT=${PROJECT:-edmhs-org}
REGION=${REGION:-us-central1}
INSTANCE=${INSTANCE:-edmhs-pg}
GITHUB_REPO=${GITHUB_REPO:?set GITHUB_REPO=owner/repo for the edmhs.org repository}
BILLING_ACCOUNT=${BILLING_ACCOUNT:?set BILLING_ACCOUNT (gcloud billing accounts list)}
HERE=$(cd "$(dirname "$0")/.." && pwd)

say(){ printf '\n== %s\n' "$*"; }
exists(){ "$@" >/dev/null 2>&1; }
rand(){ openssl rand -base64 36 | tr -d '/+=' | cut -c1-40; }

say "Project $PROJECT"
exists gcloud projects describe "$PROJECT" || gcloud projects create "$PROJECT" --name="EDMHS.org"
gcloud billing projects link "$PROJECT" --billing-account="$BILLING_ACCOUNT"
gcloud config set project "$PROJECT" >/dev/null
PNUM=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')

say "APIs"
gcloud services enable run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com iamcredentials.googleapis.com sts.googleapis.com cloudbuild.googleapis.com \
  firebase.googleapis.com firebasehosting.googleapis.com

say "Artifact Registry"
exists gcloud artifacts repositories describe edmhs --location="$REGION" || \
  gcloud artifacts repositories create edmhs --repository-format=docker --location="$REGION"

say "Cloud SQL (this step takes several minutes the first time)"
exists gcloud sql instances describe "$INSTANCE" || \
  gcloud sql instances create "$INSTANCE" --database-version=POSTGRES_16 --region="$REGION" \
    --edition=enterprise --tier=db-custom-1-3840 --storage-auto-increase \
    --backup-start-time=07:00 --enable-point-in-time-recovery --ssl-mode=ENCRYPTED_ONLY
exists gcloud sql databases describe edmhs --instance="$INSTANCE" || gcloud sql databases create edmhs --instance="$INSTANCE"
CONN="$PROJECT:$REGION:$INSTANCE"

say "Secrets"
put_secret(){ # name value  (creates once; never overwrites an existing secret)
  if exists gcloud secrets describe "$1"; then echo "secret $1 exists, keeping it"; return 1; fi
  printf '%s' "$2" | gcloud secrets create "$1" --data-file=- --replication-policy=automatic >/dev/null; echo "secret $1 created"
}
ADMIN_PW=$(rand); INTAKE_PW=$(rand); ANA_PW=$(rand)
NEW_DB_USERS=0
put_secret INTAKE_DATABASE_URL "postgresql://ict_api:${INTAKE_PW}@/edmhs?host=/cloudsql/${CONN}" && NEW_DB_USERS=1 || true
put_secret ANALYTICS_DATABASE_URL "postgresql://ana_api:${ANA_PW}@/edmhs?host=/cloudsql/${CONN}" || true
put_secret PII_KEY "$(openssl rand -base64 48)" || true

if [ "$NEW_DB_USERS" = 1 ]; then
  say "Schema + login roles (via Cloud SQL Auth Proxy)"
  command -v cloud-sql-proxy >/dev/null || { echo "Install cloud-sql-proxy first: https://cloud.google.com/sql/docs/postgres/sql-proxy"; exit 1; }
  gcloud sql users set-password postgres --instance="$INSTANCE" --password="$ADMIN_PW"
  cloud-sql-proxy --port 6543 "$CONN" & PROXY=$!; trap 'kill $PROXY 2>/dev/null' EXIT; sleep 6
  export PGHOST=127.0.0.1 PGPORT=6543 PGUSER=postgres PGPASSWORD="$ADMIN_PW" PGDATABASE=edmhs
  psql -v ON_ERROR_STOP=1 -q -f "$HERE/db/init/001_schema.sql" -f "$HERE/db/init/002_seed.sql"
  psql -v ON_ERROR_STOP=1 -q <<SQL
CREATE ROLE ict_api LOGIN PASSWORD '${INTAKE_PW}' IN ROLE edm_intake;
CREATE ROLE ana_api LOGIN PASSWORD '${ANA_PW}' IN ROLE edm_analyst;
SQL
  echo "Database admin (postgres) password, store it in your password manager now:"; echo "  $ADMIN_PW"
fi

say "Service accounts"
RUNTIME_SA="edmhs-api@${PROJECT}.iam.gserviceaccount.com"
DEPLOY_SA="github-deployer@${PROJECT}.iam.gserviceaccount.com"
exists gcloud iam service-accounts describe "$RUNTIME_SA" || gcloud iam service-accounts create edmhs-api --display-name="EDMHS API (Cloud Run)"
exists gcloud iam service-accounts describe "$DEPLOY_SA" || gcloud iam service-accounts create github-deployer --display-name="GitHub Actions deployer"
for r in roles/cloudsql.client roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$RUNTIME_SA" --role="$r" --condition=None >/dev/null
done
for r in roles/run.admin roles/artifactregistry.writer roles/firebasehosting.admin roles/cloudbuild.builds.editor \
         roles/storage.admin roles/serviceusage.serviceUsageConsumer roles/firebase.viewer; do
  gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$DEPLOY_SA" --role="$r" --condition=None >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --member="serviceAccount:$DEPLOY_SA" --role=roles/iam.serviceAccountUser >/dev/null

say "Workload Identity Federation for $GITHUB_REPO"
exists gcloud iam workload-identity-pools describe github --location=global || \
  gcloud iam workload-identity-pools create github --location=global --display-name="GitHub Actions"
exists gcloud iam workload-identity-pools providers describe github-oidc --workload-identity-pool=github --location=global || \
  gcloud iam workload-identity-pools providers create-oidc github-oidc --workload-identity-pool=github --location=global \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository == '${GITHUB_REPO}' && assertion.ref == 'refs/heads/main'"
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PNUM}/locations/global/workloadIdentityPools/github/attribute.repository/${GITHUB_REPO}" >/dev/null

say "Firebase"
npx -y firebase-tools@13.29.1 projects:addfirebase "$PROJECT" 2>/dev/null || echo "(Firebase already enabled on $PROJECT)"
npx -y firebase-tools@13.29.1 hosting:sites:create edmhs-org --project "$PROJECT" 2>/dev/null || echo "(Hosting site edmhs-org already exists)"

say "Done. Add these as GitHub Actions variables on $GITHUB_REPO (Settings > Secrets and variables > Actions > Variables):"
cat <<EOF
  GCP_PROJECT            = $PROJECT
  GCP_REGION             = $REGION
  CLOUDSQL_CONNECTION    = $CONN
  WIF_PROVIDER           = projects/${PNUM}/locations/global/workloadIdentityPools/github/providers/github-oidc
  DEPLOY_SERVICE_ACCOUNT = $DEPLOY_SA
  RUNTIME_SERVICE_ACCOUNT= $RUNTIME_SA

Then: Firebase console > Hosting > edmhs-org > Add custom domain > edmhs.org (and www.edmhs.org),
and add the DNS records it shows at your domain registrar.
EOF
