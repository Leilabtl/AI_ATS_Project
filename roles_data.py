"""
Pre-defined role list and job description templates for HR Compass ATS.
Each JD is a realistic, substantial template an HR manager can use as-is or edit.
"""

# ── Seniority ─────────────────────────────────────────────────────────────────
SENIORITY_LEVELS: list[str] = [
    "Intern",
    "Junior",
    "Mid-Level",
    "Senior",
    "Lead",
    "Principal",
    "Staff",
]

# Prepended to the JD when a seniority level is selected.
# Contains keywords that drive seniority_alignment scoring correctly.
SENIORITY_CONTEXT: dict[str, str] = {
    "Intern": (
        "Seniority Level: Intern\n"
        "This is an internship position for students or recent graduates (0 years of "
        "professional experience). The intern will work under close supervision on "
        "defined tasks, gaining hands-on experience. Entry-level commitment; structured "
        "mentorship and onboarding are provided throughout the placement."
    ),
    "Junior": (
        "Seniority Level: Junior (Entry-Level)\n"
        "This is a junior entry-level role for candidates with 0–2 years of professional "
        "experience. Strong foundational knowledge is required. The candidate will work "
        "closely with senior colleagues, receive regular mentorship, and is expected to "
        "grow rapidly into independent delivery."
    ),
    "Mid-Level": (
        "Seniority Level: Mid-Level (3–5 years experience)\n"
        "This is a mid-level intermediate role for candidates with 3–5 years of "
        "professional experience. Mid-level professionals are expected to work "
        "independently on well-scoped tasks, contribute meaningfully to team design "
        "discussions, and support less-experienced colleagues. Solid intermediate "
        "proficiency across core requirements is essential."
    ),
    "Senior": (
        "Seniority Level: Senior (5–8 years experience)\n"
        "This is a senior-level role requiring 5–8 years of professional experience. "
        "Senior candidates lead technical decisions within their domain, provide "
        "mentorship to developing colleagues, and deliver complex projects with "
        "minimal supervision. Deep expert-level mastery of core technologies is "
        "expected. The role demands senior expertise and architectural thinking."
    ),
    "Lead": (
        "Seniority Level: Lead (8+ years experience)\n"
        "This is a lead-level role requiring 8+ years of professional experience. "
        "The Lead owns the technical direction for their squad or domain, drives "
        "engineering standards and best practices, coaches developing team members, "
        "and partners with management on roadmap prioritisation. Demonstrated "
        "senior leadership and architectural decision-making is required."
    ),
    "Principal": (
        "Seniority Level: Principal (10+ years experience)\n"
        "This is a principal-level individual contributor role requiring 10+ years of "
        "professional experience. Scope spans multiple teams or product areas. The "
        "Principal drives architectural decisions, defines engineering standards at "
        "department level, and resolves the most complex technical challenges. Expert "
        "mastery and a proven track record of cross-team technical leadership is "
        "essential. This is a senior staff-level position."
    ),
    "Staff": (
        "Seniority Level: Staff (10+ years experience)\n"
        "This is a staff-level individual contributor role requiring 10+ years of "
        "experience with company-wide technical impact. The Staff engineer sets "
        "technical strategy, aligns cross-functional engineering teams, and operates "
        "with executive-level visibility. Influence extends beyond any single team, "
        "shaping the direction of the entire engineering organisation. Senior "
        "principal-level authority and impact is expected."
    ),
}


ROLES: dict[str, str] = {

# ════════════════════════════════════════════════════════════════════════════
#  ENGINEERING – BACKEND / PLATFORM
# ════════════════════════════════════════════════════════════════════════════

"Senior Python Developer": """
Role Overview
We are looking for a Senior Python Developer to design, build, and maintain scalable backend services and data pipelines. You will work closely with product, data, and infrastructure teams to deliver reliable, high-performance systems.

Key Responsibilities
- Design and implement RESTful APIs and microservices using Python frameworks (FastAPI, Django, Flask)
- Optimize database queries and schema design across PostgreSQL and Redis
- Write clean, testable code with high unit- and integration-test coverage (pytest)
- Participate in code reviews and mentor junior developers
- Collaborate with DevOps to containerize services (Docker / Kubernetes) and improve CI/CD pipelines
- Monitor production systems and troubleshoot performance bottlenecks
- Contribute to architectural decisions and technical documentation

Required Skills
- 5+ years of professional Python development
- Strong proficiency in FastAPI or Django REST Framework
- Solid understanding of SQL (PostgreSQL), NoSQL (Redis, MongoDB)
- Experience with Docker, Kubernetes, and cloud platforms (AWS or GCP)
- Familiarity with CI/CD tools (GitHub Actions, Jenkins)
- Understanding of asynchronous programming (asyncio, Celery)

Nice to Have
- Experience with Apache Kafka or similar message-queue systems
- Contributions to open-source Python projects
- AWS Certified Developer or equivalent certification

Qualifications
- Bachelor's or Master's degree in Computer Science or equivalent experience
- 5+ years of Python backend development in production environments
""".strip(),

"Backend Engineer": """
Role Overview
We are hiring a Backend Engineer to build and scale the server-side systems that power our platform. You will own services from design to deployment, ensuring high availability and maintainability.

Key Responsibilities
- Develop and maintain microservices in Python, Go, or Java
- Design RESTful and GraphQL API contracts in collaboration with frontend and mobile teams
- Model relational and document database schemas optimised for read/write patterns
- Write comprehensive unit, integration, and load tests
- Investigate and resolve production incidents using observability tooling (Datadog, Grafana)
- Participate in on-call rotation and post-mortems

Required Skills
- 3+ years of backend engineering experience
- Proficiency in at least one of: Python, Go, Java, Node.js
- Strong SQL skills (PostgreSQL or MySQL)
- Experience with REST API design best practices
- Familiarity with Docker and cloud deployment (AWS, Azure, or GCP)
- Understanding of concurrency patterns and caching strategies

Nice to Have
- Experience with event-driven architecture (Kafka, RabbitMQ)
- gRPC / Protocol Buffers
- Infrastructure as Code (Terraform, Ansible)

Qualifications
- Bachelor's degree in Computer Science or related field, or equivalent practical experience
- Demonstrated track record of shipping production backend systems
""".strip(),

"Full Stack Developer": """
Role Overview
We need a Full Stack Developer who can move fluently between React frontends and Python/Node backends, shipping complete features end-to-end with minimal handoffs.

Key Responsibilities
- Build responsive user interfaces with React (hooks, context, TypeScript)
- Develop and maintain backend APIs (Python/FastAPI or Node.js/Express)
- Design database schemas (PostgreSQL) and write optimised queries
- Implement authentication flows (OAuth 2.0, JWT)
- Write automated tests across the full stack (Jest, pytest, Cypress)
- Manage deployments through CI/CD pipelines on AWS or GCP
- Collaborate with designers to turn Figma mockups into pixel-perfect UIs

Required Skills
- 3+ years of full-stack development experience
- Strong proficiency in React / TypeScript and a backend language (Python or Node.js)
- SQL database design and query optimisation
- Familiarity with REST APIs and GraphQL
- Version control with Git and experience with pull-request workflows

Nice to Have
- Experience with Next.js or a similar SSR framework
- WebSocket / real-time features
- AWS (Lambda, S3, RDS) or GCP experience

Qualifications
- Bachelor's degree in Computer Science or equivalent practical experience
- Portfolio demonstrating end-to-end product delivery
""".strip(),

"Frontend Engineer": """
Role Overview
We are looking for a Frontend Engineer with a strong sense of UX to build fast, accessible, and visually polished web applications that delight millions of users.

Key Responsibilities
- Build and maintain component libraries and design systems in React and TypeScript
- Optimise Core Web Vitals (LCP, CLS, FID) and implement performance budgets
- Collaborate with UX/Product to translate Figma designs into interactive experiences
- Write comprehensive unit (Jest/RTL) and end-to-end (Playwright/Cypress) tests
- Implement state management solutions (Redux, Zustand, React Query)
- Ensure WCAG 2.1 AA accessibility compliance across all interfaces
- Participate in design reviews and contribute to front-end architecture decisions

Required Skills
- 3+ years of professional frontend development
- Expert-level React and TypeScript
- CSS-in-JS or Tailwind CSS, responsive layout
- Performance profiling and optimisation experience
- Familiarity with CI/CD and deployment pipelines

Nice to Have
- GraphQL / Apollo Client experience
- Micro-frontend architecture
- Animation libraries (Framer Motion, GSAP)

Qualifications
- Bachelor's degree in Computer Science, Design, or equivalent
- Demonstrable portfolio of production UI projects
""".strip(),

"DevOps Engineer": """
Role Overview
We are looking for a DevOps Engineer to build and maintain the infrastructure, tooling, and practices that let our engineering teams ship faster and more reliably.

Key Responsibilities
- Design, implement, and maintain CI/CD pipelines (GitHub Actions, Jenkins, GitLab CI)
- Manage cloud infrastructure on AWS or Azure using Terraform and Ansible
- Administer Kubernetes clusters: autoscaling, network policies, Helm chart management
- Implement observability stacks (Prometheus, Grafana, ELK, Datadog)
- Drive security best practices: IAM policies, secret management (Vault), SAST/DAST
- Respond to infrastructure incidents and conduct blameless post-mortems
- Partner with development teams to reduce toil through automation

Required Skills
- 3+ years of DevOps / platform engineering experience
- Proficiency in Terraform or Pulumi for infrastructure as code
- Strong Kubernetes administration skills (CKA preferred)
- CI/CD pipeline design and maintenance
- Scripting in Bash and Python
- Cloud platform expertise (AWS, Azure, or GCP)

Nice to Have
- GitOps workflows (ArgoCD, Flux)
- Service mesh experience (Istio, Linkerd)
- Chaos engineering practices

Qualifications
- Bachelor's degree in Computer Science or related field
- AWS/Azure/GCP certification or equivalent hands-on experience
""".strip(),

"Platform / SRE Engineer": """
Role Overview
We need a Platform / Site Reliability Engineer to own the reliability, scalability, and efficiency of our production systems, applying software engineering principles to infrastructure problems.

Key Responsibilities
- Define and track Service Level Objectives (SLOs) and error budgets with product teams
- Build internal developer platforms, self-service tooling, and golden-path templates
- Perform capacity planning and manage autoscaling policies for Kubernetes workloads
- Automate runbooks and reduce mean time to recovery (MTTR) through engineering
- Champion observability: structured logging, distributed tracing (OpenTelemetry), alerting
- Lead production readiness reviews before major feature launches
- Drive blameless post-mortems and systemic reliability improvements

Required Skills
- 4+ years of SRE or platform engineering experience
- Deep Kubernetes expertise and cloud platforms (AWS, GCP, or Azure)
- Strong programming skills (Go, Python)
- Infrastructure as Code (Terraform)
- Experience with observability tools (Prometheus, Grafana, Jaeger)

Nice to Have
- Chaos engineering (Chaos Monkey, Gremlin)
- FinOps / cloud cost optimisation
- Multi-region distributed systems experience

Qualifications
- Bachelor's or Master's degree in Computer Science or related field
- Google SRE certification or CKA/CKS preferred
""".strip(),

"Cloud Architect": """
Role Overview
We are seeking a Cloud Architect to lead the design of our cloud-native infrastructure, ensuring scalability, security, and cost efficiency across multi-cloud and hybrid environments.

Key Responsibilities
- Define and document cloud reference architectures for AWS, Azure, or GCP
- Lead migration of legacy workloads to cloud-native architectures (lift-and-shift, re-platform, re-architect)
- Design disaster recovery and business continuity strategies (RPO/RTO targets)
- Establish cloud governance frameworks: tagging policies, cost allocation, security baselines
- Evaluate and recommend cloud services, third-party vendors, and tooling
- Mentor engineering teams on cloud best practices and patterns
- Collaborate with InfoSec to ensure SOC 2 / ISO 27001 alignment

Required Skills
- 6+ years of cloud engineering / architecture experience
- Deep expertise in at least one major cloud platform (AWS, Azure, or GCP)
- Infrastructure as Code (Terraform, CDK, or Pulumi)
- Container orchestration (Kubernetes, EKS/AKS/GKE)
- Networking fundamentals (VPC, VPN, Direct Connect, peering)
- Cloud security architecture (IAM, KMS, WAF, GuardDuty)

Nice to Have
- FinOps Certified Practitioner
- Multi-cloud architecture experience
- TOGAF or equivalent enterprise architecture framework

Qualifications
- AWS Solutions Architect Professional / GCP Professional Cloud Architect / Azure Solutions Expert
- Bachelor's or Master's degree in Computer Science or related field
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  ENGINEERING – DATA / AI / ML
# ════════════════════════════════════════════════════════════════════════════

"Data Scientist": """
Role Overview
We are looking for a Data Scientist to transform complex datasets into actionable insights, predictive models, and data-driven products that directly influence business decisions.

Key Responsibilities
- Develop, validate, and deploy machine learning models (regression, classification, NLP, recommendation)
- Design and run A/B experiments and evaluate statistical significance of outcomes
- Build data pipelines to extract, clean, and feature-engineer large datasets using Python and SQL
- Communicate findings clearly to non-technical stakeholders through visualisations and reports
- Collaborate with engineering to productionise models via REST APIs or batch pipelines
- Monitor deployed models for drift and retrain as required
- Stay current with state-of-the-art research and evaluate applicability to business problems

Required Skills
- 3+ years of data science or machine learning experience
- Proficiency in Python (Pandas, NumPy, scikit-learn, PyTorch or TensorFlow)
- Strong SQL skills for data extraction and transformation
- Experience with statistical analysis and hypothesis testing
- Familiarity with MLOps tools (MLflow, DVC, Weights & Biases)
- Clear written and verbal communication of complex findings

Nice to Have
- Experience with large-scale distributed computing (Spark, Databricks)
- NLP / LLM fine-tuning experience
- Cloud ML platforms (SageMaker, Vertex AI)

Qualifications
- Master's or PhD in Statistics, Mathematics, Computer Science, or a quantitative field
- Track record of models shipped to production
""".strip(),

"AI/ML Engineer": """
Role Overview
We are hiring an AI/ML Engineer to design, train, and deploy machine learning systems at scale. You will bridge the gap between research and production, ensuring models are reliable, efficient, and maintainable.

Key Responsibilities
- Research and implement state-of-the-art ML architectures (transformers, CNNs, RNNs, diffusion models)
- Build end-to-end ML pipelines: data ingestion, feature engineering, training, evaluation, deployment
- Deploy models to production via REST APIs, streaming inference, or batch pipelines on cloud platforms
- Implement MLOps practices: model versioning (DVC/MLflow), CI/CD for models, drift monitoring
- Optimise model performance (quantisation, distillation, TensorRT) for latency and throughput targets
- Collaborate with data engineers to ensure training data quality and pipeline reliability
- Write technical design documents and conduct model review sessions

Required Skills
- 3+ years of ML engineering experience
- Deep proficiency in Python and ML frameworks (PyTorch, TensorFlow, or JAX)
- Strong understanding of model architectures: CNNs, RNNs, Transformers, GANs
- Experience deploying models to cloud platforms (AWS SageMaker, GCP Vertex AI, or Azure ML)
- Familiarity with Docker, Kubernetes, and CI/CD pipelines
- Strong software engineering practices (testing, code review, documentation)

Nice to Have
- LLM fine-tuning and RLHF experience
- Vector databases (Pinecone, Milvus, Weaviate) for RAG pipelines
- Rust or C++ for low-latency inference optimisation

Qualifications
- Master's or PhD in Computer Science, AI, or related quantitative field
- 3+ years of ML models in production
""".strip(),

"Data Engineer": """
Role Overview
We are seeking a Data Engineer to build and maintain the data infrastructure that powers our analytics, machine learning, and business intelligence capabilities.

Key Responsibilities
- Design, build, and optimise ETL/ELT pipelines using Apache Spark, Airflow, and dbt
- Architect and maintain data warehouse solutions (Snowflake, BigQuery, or Redshift)
- Implement data quality checks, lineage tracking, and observability (Great Expectations, Monte Carlo)
- Build real-time streaming pipelines using Kafka and Flink
- Collaborate with data scientists and analysts to model data for analytical consumption
- Define and enforce data governance standards, access controls, and PII handling policies
- Optimise query performance and manage compute costs on cloud data platforms

Required Skills
- 3+ years of data engineering experience
- Strong Python and SQL proficiency
- Experience with Apache Spark and distributed computing frameworks
- Workflow orchestration with Airflow, Prefect, or Dagster
- Cloud data warehouse expertise (Snowflake, BigQuery, or Redshift)
- Event streaming with Kafka or Kinesis

Nice to Have
- dbt (data build tool) certification
- Data mesh or data product architecture experience
- Streaming SQL with Flink or Spark Structured Streaming

Qualifications
- Bachelor's or Master's degree in Computer Science, Engineering, or related field
- Demonstrable experience building production data pipelines at scale
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  ENGINEERING – SPECIALISED
# ════════════════════════════════════════════════════════════════════════════

"Cybersecurity Engineer": """
Role Overview
We are looking for a Cybersecurity Engineer to protect our systems, data, and users from threats by implementing security controls, performing assessments, and driving a security-first engineering culture.

Key Responsibilities
- Conduct vulnerability assessments and penetration tests across web, mobile, and cloud infrastructure
- Design and implement security controls: WAF, IDS/IPS, SIEM, EDR, secrets management (Vault)
- Lead threat modelling sessions for new features and architectural changes
- Manage incident response: detection, containment, eradication, and post-incident review
- Define secure-by-default development standards and train engineering teams
- Ensure compliance with frameworks: SOC 2, ISO 27001, GDPR, PCI-DSS
- Monitor security tooling and investigate alerts 24/7 through SIEM platforms

Required Skills
- 4+ years of cybersecurity engineering or penetration testing experience
- Proficiency with security tools: Burp Suite, Nessus, Metasploit, Wireshark
- Cloud security expertise (AWS Security Hub, Azure Defender, GCP Security Command Center)
- Strong scripting skills (Python, Bash) for automation and tooling
- Deep understanding of OWASP Top 10 and CVE remediation workflows
- Networking fundamentals: TCP/IP, DNS, TLS, firewall rule sets

Nice to Have
- CISSP, CEH, OSCP, or AWS Security Specialty certification
- Secure SDLC / DevSecOps pipeline implementation
- Threat intelligence platforms (MISP, OpenCTI)

Qualifications
- Bachelor's degree in Cybersecurity, Computer Science, or related field
- Relevant certifications (CISSP, CEH, OSCP, or equivalent)
""".strip(),

"Mobile Developer (iOS/Android)": """
Role Overview
We are hiring a Mobile Developer to build high-quality, performant native or cross-platform mobile applications that serve millions of users on iOS and Android.

Key Responsibilities
- Develop and maintain mobile applications using Swift (iOS), Kotlin (Android), or Flutter/React Native
- Collaborate with designers to implement pixel-perfect, accessible UI components
- Integrate mobile apps with REST and GraphQL backend APIs
- Write comprehensive unit and UI tests (XCTest, Espresso, Flutter Test)
- Optimise app performance: startup time, memory usage, battery consumption
- Manage app releases through App Store and Google Play Store pipelines
- Investigate and resolve crash reports via Firebase Crashlytics or Sentry

Required Skills
- 3+ years of mobile development experience
- Proficiency in Swift/SwiftUI (iOS) or Kotlin/Jetpack Compose (Android), or Flutter
- Experience with RESTful API integration and async programming patterns
- Familiarity with mobile CI/CD pipelines (Fastlane, Bitrise, Codemagic)
- Understanding of platform-specific design guidelines (HIG, Material Design)

Nice to Have
- Cross-platform development with Flutter or React Native
- Push notifications, deep linking, and background processing
- App performance profiling (Instruments, Android Profiler)

Qualifications
- Bachelor's degree in Computer Science or equivalent practical experience
- Published apps in App Store or Google Play Store
""".strip(),

"QA Engineer": """
Role Overview
We are looking for a QA Engineer to champion software quality across our product through systematic test design, automation, and close collaboration with engineering and product teams.

Key Responsibilities
- Design, implement, and maintain automated test suites: unit, integration, API, and end-to-end (Pytest, Selenium, Playwright, Cypress)
- Perform exploratory, regression, and performance testing across web, mobile, and API layers
- Define test plans and acceptance criteria in collaboration with Product Managers
- Integrate automated tests into CI/CD pipelines and track quality metrics (coverage, flakiness, MTTR)
- Identify, document, and track defects with clear reproduction steps and severity classification
- Participate in architecture reviews to identify testability risks early
- Advocate for shift-left testing practices across engineering teams

Required Skills
- 3+ years of QA / test automation engineering experience
- Proficiency in at least one test automation framework: Playwright, Cypress, Selenium, or Appium
- Strong Python or JavaScript scripting for test tooling
- API testing with Postman, REST Assured, or similar
- SQL for database validation and data integrity checks
- Experience with CI/CD pipelines (GitHub Actions, Jenkins)

Nice to Have
- Performance testing with k6, Gatling, or JMeter
- Contract testing (Pact)
- ISTQB or similar certification

Qualifications
- Bachelor's degree in Computer Science, Software Engineering, or related field
- Demonstrable track record of reducing defect escape rate in production
""".strip(),

"Embedded Systems Engineer": """
Role Overview
We are seeking an Embedded Systems Engineer to develop firmware and low-level software for IoT devices, microcontrollers, and real-time systems in a safety-critical or consumer electronics environment.

Key Responsibilities
- Develop firmware in C and C++ for ARM-based microcontrollers (STM32, Nordic nRF, ESP32)
- Design and implement RTOS-based applications (FreeRTOS, Zephyr) with hard real-time constraints
- Write hardware abstraction layers (HAL) and board support packages (BSP)
- Integrate communication protocols: I2C, SPI, UART, CAN, BLE, LoRa, MQTT
- Collaborate with hardware engineers on PCB bring-up, signal integrity, and validation
- Develop automated test frameworks for embedded target hardware (HIL testing)
- Optimise for power consumption, flash footprint, and RAM usage

Required Skills
- 4+ years of embedded firmware development
- Expert-level C and C++ for resource-constrained environments
- RTOS development (FreeRTOS, Zephyr, or similar)
- Hands-on experience with debuggers/JTAG (J-Link, OpenOCD) and oscilloscopes
- Communication protocols: UART, SPI, I2C, CAN, USB
- Understanding of low-power design and battery-operated device constraints

Nice to Have
- Rust for embedded systems
- Safety standards (IEC 61508, ISO 26262, or IEC 62443)
- Wireless protocols (BLE, LoRaWAN, Thread, Zigbee)

Qualifications
- Bachelor's degree in Electrical Engineering, Computer Engineering, or related field
- Proven firmware shipped to mass-production hardware products
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  PRODUCT / MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

"Product Manager": """
Role Overview
We are looking for a Product Manager to define, prioritise, and drive the delivery of impactful features that solve real customer problems and align with our strategic objectives.

Key Responsibilities
- Own the product roadmap for one or more product areas: gather inputs, prioritise, communicate, and maintain alignment across stakeholders
- Write crisp product requirements documents (PRDs) and user stories with clear acceptance criteria
- Partner with UX Research to conduct user interviews, usability tests, and synthesise findings
- Define success metrics (KPIs, OKRs) and track product performance through dashboards
- Facilitate sprint planning, backlog grooming, and retrospectives alongside the engineering team
- Coordinate cross-functional go-to-market launches with Marketing, Sales, and Customer Success
- Make data-driven prioritisation decisions using quantitative analysis (SQL, product analytics tools)

Required Skills
- 4+ years of product management experience, preferably in a B2B or B2C SaaS environment
- Strong analytical skills with experience in product analytics tools (Amplitude, Mixpanel, Looker)
- Excellent written and verbal communication; ability to influence without authority
- Experience with agile methodologies and tools (Jira, Linear, Confluence)
- Ability to translate ambiguous customer needs into concrete product solutions
- Comfort working closely with engineers and understanding technical constraints

Nice to Have
- Technical background (engineering, data science)
- Experience with SQL for self-serve data analysis
- Familiarity with A/B testing platforms (Optimizely, LaunchDarkly)

Qualifications
- Bachelor's degree (MBA is a plus)
- Demonstrable product launches with measurable customer impact
""".strip(),

"Project Manager": """
Role Overview
We are hiring a Project Manager to plan, execute, and close technology projects on time, within scope, and within budget while coordinating cross-functional teams and managing stakeholder expectations.

Key Responsibilities
- Define project scope, objectives, deliverables, and success criteria in collaboration with stakeholders
- Build detailed project plans including timelines, resource requirements, and risk registers
- Track project progress daily; identify blockers early and implement corrective actions
- Facilitate regular project status meetings, standups, and steering committee reviews
- Manage risks, dependencies, change requests, and escalation paths
- Coordinate internal and third-party vendors; manage contracts and SLAs
- Produce clear status reports and executive dashboards

Required Skills
- 4+ years of project management experience in technology or software delivery
- PMP, PRINCE2, or equivalent project management certification
- Proficiency with project management tools: Jira, MS Project, Asana, or Smartsheet
- Strong stakeholder communication and facilitation skills
- Experience managing projects using both waterfall and agile methodologies
- Risk management and issue resolution

Nice to Have
- Experience in Agile/SAFe environments
- Technical background or understanding of software development lifecycle
- Budget management and vendor negotiation experience

Qualifications
- Bachelor's degree in Business Administration, Computer Science, or related field
- PMP / PRINCE2 / AgilePM certification strongly preferred
""".strip(),

"Scrum Master / Agile Coach": """
Role Overview
We are looking for a Scrum Master or Agile Coach to guide engineering teams to high performance through servant leadership, agile best practices, and continuous improvement.

Key Responsibilities
- Facilitate all Scrum ceremonies: sprint planning, daily standups, reviews, and retrospectives
- Shield the team from interruptions and remove impediments that block progress
- Coach team members on agile values, principles, and practices
- Track and visualise team metrics: velocity, cycle time, lead time, and sprint burndown
- Identify and address team dynamics, communication gaps, and collaboration antipatterns
- Partner with Product Owners to maintain a healthy, well-refined backlog
- Scale agile practices across multiple teams in a SAFe or LeSS environment

Required Skills
- 3+ years of Scrum Master or Agile Coach experience
- Certified Scrum Master (CSM) or SAFe Scrum Master certification
- Strong facilitation and conflict resolution skills
- Experience with agile tooling (Jira, Azure DevOps, or similar)
- Servant leadership mindset with strong emotional intelligence

Nice to Have
- SAFe Program Consultant (SPC) or RTE experience
- Lean / Kanban experience
- Background in software engineering

Qualifications
- CSM, PSM, or SAFe certification required
- Bachelor's degree in any field
""".strip(),

"Business Analyst": """
Role Overview
We are looking for a Business Analyst to bridge the gap between business stakeholders and technology teams by translating complex requirements into clear, actionable specifications.

Key Responsibilities
- Elicit, analyse, and document business requirements through workshops, interviews, and process observation
- Produce Business Requirements Documents (BRDs), functional specifications, use cases, and process flow diagrams
- Work with product and engineering teams to define and prioritise epics, features, and user stories
- Facilitate UAT (User Acceptance Testing) sessions and coordinate sign-off with business owners
- Analyse current-state processes and identify improvement opportunities (As-Is / To-Be modelling)
- Track requirements traceability throughout the delivery lifecycle
- Support change management and stakeholder communication for solution rollouts

Required Skills
- 3+ years of business analysis experience in a technology or consulting environment
- Proficiency in process mapping tools (Visio, Lucidchart, BPMN)
- Experience with requirements management tools (Jira, Confluence, Azure DevOps)
- Strong SQL skills for data analysis and validation
- Stakeholder management and workshop facilitation
- Understanding of agile and waterfall SDLC methodologies

Nice to Have
- CBAP (Certified Business Analysis Professional) certification
- Experience with ERP systems (SAP, Oracle, or Microsoft Dynamics)
- Six Sigma or Lean process improvement background

Qualifications
- Bachelor's degree in Business Administration, Information Systems, or related field
- CBAP or CCBA certification preferred
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  HR / PEOPLE
# ════════════════════════════════════════════════════════════════════════════

"HR Analyst": """
Role Overview
We are seeking an HR Analyst to support data-driven people decisions through workforce reporting, HR metrics, and system administration. You will be a key partner in translating HR data into actionable insights for HR leadership and business units.

Key Responsibilities
- Collect, clean, and maintain employee data across HRIS platforms (Workday, BambooHR, or ADP)
- Build and maintain HR dashboards and reports tracking KPIs: headcount, attrition, time-to-fill, absenteeism
- Conduct trend analysis on workforce data to identify patterns and support strategic planning
- Assist with compensation benchmarking, salary band reviews, and pay equity analyses
- Support the HR team with compliance reporting (EEO-1, VETS-100, GDPR data requests)
- Drive process improvement initiatives to streamline HR operations and reduce manual effort
- Partner with Finance on headcount planning and workforce cost modelling

Required Skills
- 2+ years of HR analytics or HRIS administration experience
- Proficiency in Microsoft Excel (pivot tables, VLOOKUP, Power Query) and SQL for data queries
- Experience with at least one HRIS platform: Workday, BambooHR, ADP, or SuccessFactors
- Data visualisation with Tableau, Power BI, or similar tools
- Strong attention to detail and ability to manage sensitive employee data with discretion
- Understanding of HR processes: recruitment, onboarding, performance management, compensation

Nice to Have
- HR analytics tools (Visier, Crunchr, or similar people analytics platforms)
- Python for HR data automation
- SHRM-CP or PHR certification

Qualifications
- Bachelor's degree in Human Resources, Business Administration, or a quantitative field
- 2+ years of experience in an HR data or analytics role
""".strip(),

"HR Manager": """
Role Overview
We are hiring an HR Manager to lead the day-to-day people operations for a team of 100-500 employees. You will partner with business leaders to deliver HR strategies that attract, develop, and retain top talent.

Key Responsibilities
- Partner with business leaders to understand workforce needs and translate them into HR strategies
- Own the full employee lifecycle: recruitment, onboarding, performance management, development, and offboarding
- Manage complex employee relations cases: investigations, disciplinary processes, and grievance resolution
- Administer compensation reviews, benchmark roles, and advise on pay equity
- Ensure compliance with local labour law, company policies, and regulatory requirements (GDPR, employment law)
- Implement and improve HRIS processes and maintain accurate workforce data
- Lead HR projects: engagement surveys, culture initiatives, diversity and inclusion programmes

Required Skills
- 5+ years of HR generalist or HR business partner experience
- Deep knowledge of employment law and HR compliance
- Experience with HRIS systems (Workday, SAP, or BambooHR)
- Strong employee relations and conflict resolution skills
- Data literacy: comfort with HR metrics and workforce analytics
- Excellent interpersonal and stakeholder management skills

Nice to Have
- CIPD Level 5/7 (UK) or SHRM-SCP / SPHR (US) certification
- Experience in a high-growth or international organisation
- Change management and organisational design experience

Qualifications
- Bachelor's degree in Human Resources, Psychology, Business, or related field
- CIPD or SHRM certification strongly preferred
""".strip(),

"Talent Acquisition Specialist": """
Role Overview
We are looking for a Talent Acquisition Specialist to own the end-to-end recruitment process, sourcing and selecting top talent across technical and commercial functions.

Key Responsibilities
- Partner with hiring managers to define role requirements, ideal candidate profiles, and interview processes
- Source candidates through LinkedIn Recruiter, job boards, talent communities, and referral programmes
- Screen CVs, conduct structured competency-based interviews, and shortlist candidates
- Manage candidate experience throughout the hiring funnel to ensure a positive and timely process
- Track and report recruitment metrics: time-to-fill, cost-per-hire, offer acceptance rate, source-of-hire
- Build and maintain talent pipelines for recurring and critical roles
- Coordinate employer branding initiatives, careers page content, and campus recruiting programmes

Required Skills
- 3+ years of full-cycle recruitment experience (agency or in-house)
- Proficiency with ATS platforms (Greenhouse, Lever, Workday Recruiting, or similar)
- Experience using LinkedIn Recruiter and Boolean search techniques
- Structured interview design and competency-based assessment frameworks
- Strong candidate management and stakeholder communication skills
- Data-driven approach to sourcing and pipeline management

Nice to Have
- Technical recruiting experience (engineering, data science, product)
- Employer branding and social media recruiting
- AIRS or CIR certification

Qualifications
- Bachelor's degree in Human Resources, Psychology, Business, or related field
- 3+ years of full-cycle recruitment experience
""".strip(),

"Compensation & Benefits Specialist": """
Role Overview
We are seeking a Compensation & Benefits Specialist to design, administer, and continuously improve our total rewards programmes, ensuring market competitiveness, internal equity, and legal compliance.

Key Responsibilities
- Conduct annual compensation benchmarking using external survey data (Mercer, Radford, Willis Towers Watson)
- Administer salary band structures, grade frameworks, and pay equity analyses
- Manage benefits programmes: health insurance, pension/401(k), flexible benefits, and wellbeing initiatives
- Process compensation changes (merit increases, promotions, market adjustments) through HRIS
- Support compliance with pay transparency laws, equal pay legislation, and mandatory reporting
- Partner with Finance on headcount budget planning and salary cost modelling
- Communicate total rewards packages clearly to employees and managers

Required Skills
- 3+ years of compensation, benefits, or total rewards experience
- Proficiency in compensation survey tools (Radford, Mercer, or Payscale)
- Strong Excel and analytical skills for salary modelling and data analysis
- Knowledge of payroll processes and integration with HRIS platforms
- Understanding of relevant legislation: equal pay, pay transparency, pensions, tax implications

Nice to Have
- CCP (Certified Compensation Professional) or GRP certification
- HRIS administration experience (Workday Compensation module)
- Global or multi-country compensation experience

Qualifications
- Bachelor's degree in Human Resources, Finance, or Business Administration
- WorldatWork CCP or SHRM certification preferred
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  FINANCE / ACCOUNTING
# ════════════════════════════════════════════════════════════════════════════

"Financial Analyst": """
Role Overview
We are hiring a Financial Analyst to support business decision-making through financial modelling, variance analysis, and strategic planning across our core business units.

Key Responsibilities
- Build and maintain financial models for budgeting, forecasting, and scenario planning
- Perform monthly variance analysis comparing actuals vs. budget/forecast with clear commentary
- Prepare financial reports and management packs for executive and board-level audiences
- Support the annual budgeting process: collecting inputs, consolidating submissions, and challenging assumptions
- Conduct business case analysis and ROI assessments for investment decisions
- Partner with business unit leaders to understand cost drivers and revenue performance
- Develop self-service dashboards in Power BI or Tableau for financial KPIs

Required Skills
- 2+ years of financial analysis or FP&A experience
- Advanced Excel skills (financial modelling, pivot tables, Power Query)
- Experience with financial planning tools (Anaplan, Adaptive Insights, Oracle EPM, or similar)
- Strong understanding of P&L, balance sheet, and cash flow statements
- Excellent attention to detail and analytical rigour
- Confident communicator with the ability to explain financial data to non-finance stakeholders

Nice to Have
- SQL for pulling data from ERP or data warehouse systems
- Power BI or Tableau for dashboard development
- CFA Level I or CPA/ACCA qualification in progress

Qualifications
- Bachelor's degree in Finance, Accounting, Economics, or related field
- CPA, ACCA, CIMA, or CFA qualification (or progress toward)
""".strip(),

"FP&A Analyst": """
Role Overview
We are looking for a Financial Planning & Analysis (FP&A) Analyst to partner with business leaders in delivering high-quality forecasts, budgets, and management reporting that drive strategic decisions.

Key Responsibilities
- Lead the monthly, quarterly, and annual forecasting and budgeting cycles for assigned business units
- Prepare the management reporting pack: P&L, headcount, capex, and working capital commentary
- Build rolling 12-month financial forecasts and scenario models (upside, base, downside)
- Analyse business performance: revenue drivers, cost trends, margin expansion opportunities
- Partner with accounting to ensure forecast aligns with GAAP/IFRS recognition standards
- Automate recurring reporting using SQL, Python, or Power BI
- Prepare investor-ready materials and board presentations

Required Skills
- 3+ years of FP&A experience in a corporate or consulting environment
- Advanced financial modelling skills in Excel or Google Sheets
- Proficiency with ERP systems (SAP, Oracle, or NetSuite) and financial planning tools
- Strong SQL skills for data extraction and ad-hoc analysis
- Excellent written and verbal communication of financial narratives
- Deep understanding of GAAP or IFRS financial statements

Nice to Have
- Python or R for financial automation
- Anaplan or Adaptive Insights modelling
- Experience in a public company FP&A environment

Qualifications
- Bachelor's degree in Finance, Accounting, or Economics
- CPA, ACCA, CIMA, or CFA charterholder preferred
""".strip(),

"Management Accountant": """
Role Overview
We are seeking a Management Accountant to provide accurate, timely financial information that supports operational decision-making and ensures robust financial control across the organisation.

Key Responsibilities
- Prepare monthly management accounts: P&L, balance sheet, and cash flow with commentary
- Maintain and reconcile the general ledger; perform month-end close activities
- Oversee fixed asset register, accruals, prepayments, and intercompany reconciliations
- Assist with annual statutory accounts preparation and external audit support
- Monitor budget vs. actual performance and provide variance explanations to cost centre managers
- Ensure compliance with accounting standards (GAAP / IFRS) and internal financial controls
- Identify and implement process improvements to the finance close cycle

Required Skills
- 3+ years of management accounting or financial reporting experience
- Fully qualified or part-qualified accountant (CIMA, ACCA, ACA, or CPA)
- Proficiency with accounting software (Sage, Xero, QuickBooks, NetSuite, or SAP)
- Strong Excel skills; comfortable with large datasets and reconciliations
- Knowledge of GAAP or IFRS financial reporting standards
- High attention to detail and deadline-driven approach

Nice to Have
- Power BI or Tableau for management reporting dashboards
- Experience with ERP implementation or migration
- Multi-entity or multi-currency accounting experience

Qualifications
- CIMA, ACCA, ACA, or CPA qualification (or significant progress toward completion)
- Bachelor's degree in Accounting, Finance, or related field
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  DATA & ANALYTICS
# ════════════════════════════════════════════════════════════════════════════

"Data Analyst": """
Role Overview
We are looking for a Data Analyst to turn raw data into clear, accurate, and actionable insights that inform product decisions, marketing strategies, and operational improvements.

Key Responsibilities
- Write and optimise SQL queries to extract and transform data from our data warehouse (Snowflake, BigQuery, or Redshift)
- Build and maintain self-service dashboards and reports in Tableau, Power BI, or Looker
- Conduct ad-hoc analyses to answer business questions from product, marketing, and finance stakeholders
- Define and track KPIs; own the metrics layer and ensure data accuracy and consistency
- Identify trends, anomalies, and opportunities through exploratory data analysis
- Collaborate with data engineers to improve data quality and pipeline reliability
- Present findings to non-technical audiences with clear narratives and visualisations

Required Skills
- 2+ years of data analysis experience
- Advanced SQL proficiency (window functions, CTEs, subqueries)
- Experience with BI tools: Tableau, Power BI, Looker, or Metabase
- Proficiency in Excel or Google Sheets for ad-hoc analysis
- Statistical reasoning and hypothesis testing
- Clear communication of data findings to business stakeholders

Nice to Have
- Python (Pandas, Matplotlib) for data manipulation and visualisation
- dbt for data modelling and transformation
- Experience with A/B testing frameworks

Qualifications
- Bachelor's degree in Statistics, Mathematics, Economics, Computer Science, or related field
- 2+ years of professional data analysis experience
""".strip(),

"Business Intelligence Developer": """
Role Overview
We are hiring a BI Developer to design, build, and maintain the reporting infrastructure that transforms raw data into executive dashboards, self-service analytics, and automated reports.

Key Responsibilities
- Design and implement BI dashboards and reports in Power BI, Tableau, or Looker
- Build and maintain semantic layers, data models, and calculated measures in BI tools
- Develop and optimise SQL-based data transformations and dbt models in the data warehouse
- Collaborate with business stakeholders to gather reporting requirements and translate them into technical specs
- Ensure data accuracy, consistency, and documentation across all BI assets
- Automate report distribution and scheduling workflows
- Train and support end-users in self-service analytics

Required Skills
- 3+ years of BI development experience
- Expert-level Power BI (DAX, Power Query) or Tableau (LOD expressions, data blending)
- Advanced SQL for data modelling and transformation
- Experience with cloud data warehouses (Snowflake, BigQuery, or Redshift)
- dbt or similar transformation tooling
- Understanding of data warehousing concepts (star schema, slowly changing dimensions)

Nice to Have
- Python for data pipeline automation
- Azure Data Factory or similar ETL tooling
- Microsoft Fabric or Power BI Premium capacity administration

Qualifications
- Bachelor's degree in Computer Science, Information Systems, Mathematics, or related field
- Microsoft Power BI Data Analyst Associate or Tableau Desktop Specialist certification
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  MARKETING / SALES
# ════════════════════════════════════════════════════════════════════════════

"Digital Marketing Manager": """
Role Overview
We are looking for a Digital Marketing Manager to own our digital marketing strategy — from paid media and SEO to email automation and conversion optimisation — with a data-driven approach to driving growth.

Key Responsibilities
- Plan, execute, and optimise paid campaigns across Google Ads, Meta Ads, LinkedIn, and programmatic channels
- Own the SEO strategy: technical audits, content briefs, link building, and keyword performance tracking
- Manage email marketing programmes using HubSpot or Mailchimp: segmentation, automation, A/B testing
- Track and report digital performance using GA4, Google Search Console, and marketing attribution models
- Collaborate with content, creative, and product teams to align messaging and conversion funnels
- Manage agency relationships, media buys, and campaign budgets with clear ROI accountability
- Implement CRO initiatives: landing page tests, form optimisation, checkout improvements

Required Skills
- 4+ years of digital marketing experience
- Proven expertise in Google Ads and Meta Ads campaign management and optimisation
- Strong SEO knowledge: technical SEO, on-page, and off-page strategy
- Proficiency with marketing analytics tools (GA4, Looker Studio, HubSpot)
- Email marketing and marketing automation experience
- Data-driven mindset with comfort analysing performance dashboards

Nice to Have
- Programmatic advertising (DV360, The Trade Desk)
- Video marketing (YouTube Ads, TikTok)
- Google Analytics 4 certification

Qualifications
- Bachelor's degree in Marketing, Communications, or Business
- Google Ads and/or Meta Blueprint certification preferred
""".strip(),

"SEO Specialist": """
Role Overview
We are seeking an SEO Specialist to grow organic search traffic through technical excellence, compelling content strategies, and disciplined link acquisition.

Key Responsibilities
- Conduct comprehensive technical SEO audits: crawlability, site speed, Core Web Vitals, structured data
- Perform keyword research and competitive analysis to identify content and ranking opportunities
- Produce content briefs and collaborate with writers to create SEO-optimised content
- Build and manage white-hat link acquisition campaigns (outreach, digital PR, broken link building)
- Track rankings, organic traffic, and conversion performance using SEMrush, Ahrefs, and GA4
- Implement schema markup and optimise for featured snippets and rich results
- Monitor and disavow toxic backlinks; maintain a healthy link profile

Required Skills
- 3+ years of SEO experience in a B2B or B2C environment
- Proficiency with SEO tools: Ahrefs, SEMrush, Screaming Frog, Google Search Console
- Technical SEO expertise: crawl budget, Core Web Vitals, hreflang, canonical tags
- Keyword research and content strategy experience
- Understanding of HTML, CSS, and JavaScript as they relate to SEO
- Data analysis with GA4 and Looker Studio

Nice to Have
- Local SEO and Google Business Profile optimisation
- International / multilingual SEO
- Python for SEO automation (crawling, data extraction)

Qualifications
- Bachelor's degree in Marketing, Communications, or Computer Science
- 3+ years of demonstrable SEO results (traffic growth, ranking improvements)
""".strip(),

"Content Marketing Manager": """
Role Overview
We are hiring a Content Marketing Manager to build and execute a content strategy that drives brand awareness, organic traffic, and lead generation across channels including blog, video, social, and email.

Key Responsibilities
- Develop and own the editorial content calendar aligned with product launches, campaigns, and SEO priorities
- Produce and commission long-form content: blog posts, whitepapers, case studies, ebooks, and webinars
- Collaborate with SEO to identify content gaps and optimise existing assets for organic performance
- Manage content distribution across owned, earned, and paid channels
- Work with design and video teams to produce multimedia content assets
- Measure content performance (traffic, engagement, pipeline attribution) and iterate based on data
- Manage freelance writers and content agencies: briefing, editing, and quality control

Required Skills
- 4+ years of content marketing experience
- Exceptional writing and editing skills across multiple formats and audiences
- SEO content strategy knowledge (keyword mapping, search intent, content clusters)
- Experience with CMS platforms (WordPress, Webflow, Contentful) and marketing automation (HubSpot)
- Analytics proficiency (GA4, HubSpot, or similar) to measure content ROI
- Project management skills to manage multiple content streams simultaneously

Nice to Have
- Video script writing and production coordination
- Podcast content strategy
- B2B SaaS content experience

Qualifications
- Bachelor's degree in English, Journalism, Marketing, or Communications
- Portfolio of high-performing content assets
""".strip(),

"Account Executive (Sales)": """
Role Overview
We are looking for an Account Executive to manage the full sales cycle from prospecting to close, consistently exceeding revenue quotas while building long-term customer relationships.

Key Responsibilities
- Own a defined territory or account list; develop and execute account plans for strategic growth
- Manage the full sales cycle: discovery, demo, proposal, negotiation, and contract close
- Conduct needs analysis with economic buyers and champion relationships across stakeholder levels
- Build and maintain a healthy 3x pipeline through outbound prospecting, inbound lead follow-up, and referrals
- Collaborate with Solution Engineers, Customer Success, and Marketing on complex deals
- Accurately forecast monthly and quarterly revenue in Salesforce CRM
- Negotiate contract terms, pricing, and SOWs with legal and finance involvement

Required Skills
- 3+ years of B2B SaaS or technology sales experience
- Proven track record of consistently achieving or exceeding quota
- Proficiency with Salesforce CRM and sales enablement tools (Outreach, Gong, or similar)
- Consultative selling methodology (MEDDIC, Challenger, SPIN, or similar)
- Excellent discovery, objection handling, and negotiation skills
- Ability to manage complex, multi-stakeholder deals with 3-12 month sales cycles

Nice to Have
- Experience selling into enterprise accounts ($100K+ ACV)
- Technical product (developer tools, data platforms, cybersecurity) sales background
- SaaS metrics literacy (ARR, NRR, churn)

Qualifications
- Bachelor's degree in Business, Marketing, or related field
- 3+ years of quota-carrying software sales experience
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  OPERATIONS / SUPPLY CHAIN
# ════════════════════════════════════════════════════════════════════════════

"Operations Manager": """
Role Overview
We are seeking an Operations Manager to lead the day-to-day operational functions of our business, driving efficiency, quality, and scalability across people, processes, and systems.

Key Responsibilities
- Oversee daily operational processes and ensure KPIs are met: throughput, quality, cost, and SLA compliance
- Identify and eliminate bottlenecks through process mapping, root cause analysis, and lean / six sigma techniques
- Lead, coach, and develop a team of operational staff and team leads
- Manage vendor relationships, service contracts, and third-party logistics/service providers
- Drive continuous improvement projects using data-driven methodologies
- Collaborate with finance on budgeting, cost control, and operational forecasting
- Implement SOPs and ensure regulatory and safety compliance across all operations

Required Skills
- 5+ years of operations management experience
- Proven track record of process improvement and efficiency gains (Lean, Six Sigma, or Kaizen)
- Strong data analysis skills: Excel, SQL, or BI tools for operational dashboards
- People management experience: hiring, coaching, performance management
- Project management skills and experience leading cross-functional initiatives
- Excellent communication and stakeholder management at all levels

Nice to Have
- Six Sigma Green or Black Belt certification
- Experience with ERP systems (SAP, Oracle, or Microsoft Dynamics)
- Supply chain or logistics management experience

Qualifications
- Bachelor's degree in Business Administration, Operations Management, Engineering, or related field
- PMP or Lean Six Sigma certification preferred
""".strip(),

"Supply Chain Analyst": """
Role Overview
We are hiring a Supply Chain Analyst to optimise the flow of goods, information, and capital through our supply chain by leveraging data analysis, demand planning, and process improvement.

Key Responsibilities
- Analyse supply chain data to identify inefficiencies, forecast demand, and optimise inventory levels
- Build and maintain demand planning models using historical data, market trends, and sales inputs
- Monitor supplier performance against KPIs: on-time delivery, quality, and cost
- Support procurement teams with market analysis, RFQ evaluation, and vendor scorecards
- Develop and maintain supply chain dashboards (Power BI, Tableau) for visibility and decision-making
- Coordinate with warehouse, logistics, and planning teams to resolve supply disruptions
- Model the financial impact of supply chain decisions on working capital and COGS

Required Skills
- 2+ years of supply chain analysis or planning experience
- Strong analytical and data modelling skills (Excel, SQL)
- Experience with ERP systems (SAP MM/PP, Oracle SCM, or similar)
- Understanding of supply chain concepts: S&OP, MRP, inventory optimisation, DRP
- Data visualisation (Power BI or Tableau) for operational reporting

Nice to Have
- APICS CPIM or CSCP certification
- Python for supply chain modelling and automation
- Experience with demand planning tools (Kinaxis, o9, or Blue Yonder)

Qualifications
- Bachelor's degree in Supply Chain Management, Industrial Engineering, Business, or related field
- APICS certification (CPIM or CSCP) preferred
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  DESIGN
# ════════════════════════════════════════════════════════════════════════════

"UI/UX Designer": """
Role Overview
We are looking for a UI/UX Designer to create intuitive, accessible, and visually compelling digital experiences that solve real user problems and delight customers.

Key Responsibilities
- Lead end-to-end UX design: user research, information architecture, wireframing, prototyping, and high-fidelity UI design
- Conduct user interviews, usability tests, and synthesise findings to validate design decisions
- Collaborate with Product Managers to define problem statements and success metrics before moving to design
- Build and maintain a consistent design system and component library in Figma
- Hand off production-ready designs to frontend engineers with clear specifications and interaction notes
- Conduct design reviews throughout development to ensure quality and consistency
- Champion accessibility (WCAG 2.1 AA) and inclusive design across all product surfaces

Required Skills
- 3+ years of UI/UX design experience for digital products (web and/or mobile)
- Expert proficiency in Figma (components, auto-layout, variables, prototyping)
- Strong portfolio demonstrating user-centred design process, not just visual output
- Experience conducting user research and usability testing
- Understanding of HTML/CSS constraints that affect design feasibility
- Excellent communication of design rationale to technical and non-technical audiences

Nice to Have
- Motion design and micro-interaction design (Lottie, Rive)
- Experience with design systems at scale (Storybook integration)
- Quantitative UX research: surveys, analytics, heatmaps (Hotjar, FullStory)

Qualifications
- Bachelor's degree in Design, HCI, or equivalent practical experience
- Portfolio of shipped consumer or enterprise product designs
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  LEGAL / COMPLIANCE
# ════════════════════════════════════════════════════════════════════════════

"Compliance Officer": """
Role Overview
We are seeking a Compliance Officer to develop and maintain our compliance framework, ensuring the organisation meets all regulatory, legal, and ethical obligations across its markets.

Key Responsibilities
- Develop, implement, and maintain compliance policies and procedures across the organisation
- Monitor regulatory developments (GDPR, AML, FCA, SEC, or sector-specific regulations) and advise on impact
- Conduct internal compliance audits and risk assessments; track findings and corrective actions
- Manage regulatory examinations and interface with regulators as the primary compliance contact
- Deliver compliance training programmes and awareness campaigns to staff
- Investigate compliance incidents and breaches; escalate to legal and senior management as required
- Maintain compliance monitoring programmes and regulatory registers

Required Skills
- 4+ years of compliance, legal, or regulatory experience in financial services, technology, or healthcare
- Deep knowledge of relevant regulatory frameworks (GDPR, FCA, SEC, HIPAA, or equivalent)
- Experience conducting compliance audits and risk assessments
- Excellent written communication for policy drafting and regulatory correspondence
- High ethical standards and the ability to influence behaviour at all organisational levels

Nice to Have
- ICA, CAMS, CRCM, or equivalent compliance certification
- Experience with GRC tools (RSA Archer, MetricStream, or LogicGate)
- Legal qualification (LLB, LLM) or solicitor/attorney background

Qualifications
- Bachelor's degree in Law, Business, Finance, or related field
- ICA Diploma in Compliance or CAMS certification preferred
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  CUSTOMER SUCCESS / SUPPORT
# ════════════════════════════════════════════════════════════════════════════

"Customer Success Manager": """
Role Overview
We are hiring a Customer Success Manager to build deep relationships with our customers, drive product adoption, and ensure they achieve measurable value — resulting in strong retention and expansion revenue.

Key Responsibilities
- Own a portfolio of 30-60 accounts; develop and execute success plans aligned to customer business goals
- Drive product adoption through proactive onboarding, training, and business reviews (EBRs)
- Monitor health scores, usage data, and engagement signals to identify at-risk accounts early
- Partner with Sales on renewal negotiations and expansion opportunities (upsell/cross-sell)
- Advocate for customer needs internally with Product, Engineering, and Support teams
- Resolve escalations by coordinating cross-functional resources and communicating transparently
- Deliver data-driven QBRs demonstrating ROI and product value to executive stakeholders

Required Skills
- 3+ years of Customer Success or Account Management experience in B2B SaaS
- Proven track record of high NRR (>110%) and GRR (>90%) across a customer portfolio
- Proficiency with CRM and CS platforms: Salesforce, Gainsight, Totango, or similar
- Excellent communication and executive presence for C-level interactions
- Analytical skills to interpret product usage data and build success narratives
- Strong project management and time management across multiple accounts

Nice to Have
- Technical aptitude: ability to configure integrations and troubleshoot API issues
- Experience with churn prediction models or health scoring frameworks
- Gainsight or Salesforce certifications

Qualifications
- Bachelor's degree in Business, Marketing, or related field
- 3+ years of B2B SaaS customer success experience
""".strip(),

"Technical Support Engineer": """
Role Overview
We are looking for a Technical Support Engineer to provide expert technical assistance to customers and internal teams, resolving complex product issues and contributing to the improvement of our platform's reliability and usability.

Key Responsibilities
- Investigate and resolve complex technical support tickets via ticket system, email, chat, and screen-share sessions
- Reproduce customer issues in test environments; write clear bug reports with reproduction steps for engineering
- Develop and maintain troubleshooting guides, knowledge-base articles, and runbooks
- Communicate status updates to customers promptly and empathetically throughout the resolution process
- Collaborate with Engineering on escalated cases and participate in beta testing of new releases
- Monitor support queue health: SLA compliance, CSAT, first-response time, and resolution rate
- Contribute to product improvement by surfacing customer pain points to Product and Engineering

Required Skills
- 2+ years of technical support or software engineering experience
- Proficiency in reading logs, traces, and error messages across web and API environments
- SQL skills for querying databases and investigating data issues
- Familiarity with REST APIs (Postman, curl) and web debugging (browser DevTools, Charles Proxy)
- Excellent written and verbal communication with non-technical customers
- Experience with support platforms: Zendesk, Intercom, Freshdesk, or Jira Service Management

Nice to Have
- Scripting in Python or Bash for diagnostic automation
- Cloud platform knowledge (AWS, Azure, or GCP)
- ITIL Foundation certification

Qualifications
- Bachelor's degree in Computer Science, Information Technology, or related field
- 2+ years of customer-facing technical support experience
""".strip(),

# ════════════════════════════════════════════════════════════════════════════
#  DATABASE / SOLUTION ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════

"Database Administrator": """
Role Overview
We are seeking a Database Administrator to design, implement, and maintain the database infrastructure that underpins our mission-critical applications, ensuring high availability, performance, and data integrity.

Key Responsibilities
- Administer and optimise PostgreSQL, MySQL, and Oracle database instances in production
- Monitor database performance, identify slow queries, and implement index and query optimisations
- Design backup, recovery, and disaster recovery strategies; perform regular restore tests
- Manage database security: user access controls, encryption at rest/in transit, auditing
- Plan and execute database upgrades, patching, and migrations with minimal downtime
- Collaborate with developers on schema design, query optimisation, and ORM best practices
- Manage cloud-managed database services (AWS RDS/Aurora, Azure Database, Cloud SQL)

Required Skills
- 4+ years of DBA experience with PostgreSQL and/or MySQL in production environments
- Expert-level SQL and query optimisation (EXPLAIN ANALYZE, indexing strategies)
- High availability configuration: replication, clustering, and failover
- Backup and recovery: pgBackRest, mysqldump, point-in-time recovery
- Cloud database services: AWS RDS, Azure Database, or GCP Cloud SQL
- Database security: encryption, auditing, role-based access control

Nice to Have
- NoSQL databases (MongoDB, Redis, Cassandra)
- Oracle DBA experience
- Performance testing with pgBench or sysbench

Qualifications
- Bachelor's degree in Computer Science or related field
- OCP (Oracle Certified Professional) or PostgreSQL DBA certification preferred
""".strip(),

"Solution Architect": """
Role Overview
We are looking for a Solution Architect to design end-to-end technical solutions that address complex business requirements, bridging the gap between business strategy and technical implementation.

Key Responsibilities
- Lead architectural design sessions to translate business requirements into scalable, secure, and cost-effective technical solutions
- Produce solution design documents, architecture diagrams, and technology evaluation reports
- Evaluate and select technologies, platforms, and third-party services against defined criteria
- Define integration patterns and API contracts between systems (microservices, event-driven, SOA)
- Guide development teams during implementation, providing architectural oversight and code reviews
- Manage technical risk and quality gates throughout the project delivery lifecycle
- Present solution options and trade-offs to technical and non-technical stakeholders

Required Skills
- 7+ years of software engineering or architecture experience
- Deep expertise in at least one cloud platform (AWS, Azure, or GCP) and architecture patterns
- Experience designing distributed systems, microservices, and event-driven architectures
- Understanding of integration technologies: REST, GraphQL, gRPC, message queues (Kafka, RabbitMQ)
- Security architecture: identity management, encryption, network security
- Strong communication and stakeholder management skills

Nice to Have
- TOGAF or Zachman framework certification
- AWS Solutions Architect Professional / Azure Solutions Expert
- Domain-Driven Design (DDD) or C4 modelling experience

Qualifications
- Bachelor's or Master's degree in Computer Science or related field
- AWS/Azure/GCP Professional-level certification strongly preferred
""".strip(),

}

# Sorted list for the UI dropdown
ROLE_LIST: list[str] = sorted(ROLES.keys(), key=str.lower)
