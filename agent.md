# Agent Execution Guardrails & Documentation Lifecycle

You are an autonomous full-stack development agent. To prevent development velocity from outpacing project documentation, you are strictly required to adhere to the following workflow loop. 

## 1. The Core Directive
Every time a software feature, backend refactor, database schema migration, UI adjustment, or bug fix is successfully implemented and verified, you MUST immediately update the primary repository documentation before moving on to any other task.

## 2. Post-Task Execution Protocol
Immediately after any script changes are saved and validated via your local terminal execution tools or your integrated browser subagent, trigger this documentation loop:

### Step A: Update 'project.md'
Open and edit 'project.md' to keep its structural history perfectly accurate:
- **Move Features:** Transition the newly implemented feature out of the "## Planned Features & Next Steps" roadmap block and rewrite it as a completed item.
- **Log Technical Details:** Append a clear, technically precise summary of the change under the corresponding subheader in the "## What Has Been Done" section (e.g., Database Architecture, Security & User Flow, Mobile-First Field Logging, or Office Dashboard & Reporting). Specify exactly what table, UI element, or constraint validation rule was added.
- **Maintain Sequencing:** Clean up any renumbering or re-indexing in the planned features list so the roadmap continues to flow sequentially.

### Step B: Update 'README.md'
Open and edit 'README.md' to keep the client-facing specification fresh:
- **Feature Alignments:** Ensure the "🚀 Key Features" summaries reflect the most recent production capabilities (such as shifting authentication mechanisms, layout responsiveness, or workflow review states).
- **Stack & Roadmap Cleanliness:** Update the "🛠️ Technology Stack" list if new python packages or libraries are introduced, and purge the "🔮 Future Roadmap" of completed achievements.

### Step C: Deployment & Cloud Run Environment Protocol
With every code update or feature completion, you MUST:
1. **Push & Redeploy:** Commit your changes, push to the remote repository, and redeploy the application to Google Cloud Run.
2. **Inject Environment Variables:** Ensure that environment variables (`SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`) are securely and natively injected into the Cloud Run service configuration (e.g., using `gcloud run services update ... --update-env-vars ...`). 
   - *Why?* The local `.env` file is blocked by `.dockerignore` for security. Uploading code or deploying a local folder directly to Cloud Run will spin up the container without these credentials, causing "Database client not initialized" errors unless they are explicitly injected into the service.

## 3. Enforcement Gate
- Do not mark an issue or user prompt as "Complete" until both 'project.md' and 'README.md' have been modified, saved, and structurally audited for markdown formatting errors.
- At the start of every new user prompt or sub-task iteration, read this file ('agent.md') first to ground your operational workflow requirements.

## 4. Staging Credentials for Automated Verification
When executing your autonomous browser testing subagent protocol, always utilize the following administrative credentials to log in and verify the Office Dashboard functionality:
- **Test Admin Email:** admin2@example.com
- **Test Admin Password:** Password123!