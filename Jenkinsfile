pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    parameters {
        booleanParam(name: 'DEPLOY_TO_CLOUD_RUN', defaultValue: false, description: 'Deploy image to Cloud Run after successful build')
    }

    environment {
        PROJECT_ID = 'enterprise-rag-497423'
        REGION = 'us-central1'
        AR_REPO = 'enterprise-rag'
        SERVICE_NAME = 'enterprise-rag-api'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        IMAGE_URI = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${SERVICE_NAME}:${IMAGE_TAG}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Validate Code') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m compileall app ui

                    if [ -d tests ] || find . -maxdepth 3 -type f -name 'test_*.py' | grep -q .; then
                        pip install pytest
                        pytest -q
                    else
                        echo "No tests found. Skipping pytest."
                    fi
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_URI} .'
            }
        }

        stage('Push Image to Artifact Registry') {
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                        gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
                        docker push ${IMAGE_URI}
                    '''
                }
            }
        }

        stage('Deploy to Cloud Run') {
            when {
                allOf {
                    branch 'main'
                    expression { return params.DEPLOY_TO_CLOUD_RUN }
                }
            }
            steps {
                withCredentials([file(credentialsId: 'gcp-sa-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
                        gcloud config set project ${PROJECT_ID}

                        gcloud run deploy ${SERVICE_NAME} \
                            --image ${IMAGE_URI} \
                            --platform managed \
                            --region ${REGION} \
                            --allow-unauthenticated
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Pipeline succeeded. Image: ${IMAGE_URI}"
        }
        failure {
            echo 'Pipeline failed. Check stage logs above.'
        }
    }
}
