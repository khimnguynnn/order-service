pipeline {
  agent any

  environment {
    SERVICE_NAME = 'order-service'
    REGION = 'ap-southeast-1'
    ACCOUNT_ID = '359672545978'
    ECR_REPO = "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/icetea/microservices"
    UNIT_TEST_FILE = 'test_app.py'
  }

  stages {
    stage('CHECKOUT CODE') {
      steps {
        checkout scm
      }
    }

    stage('RUN UNIT TESTS') {
      when {
        changeRequest()
      }
      steps {
        sh '''
        #!/bin/bash
        set -e
        export PATH=$PATH:$HOME/.local/bin
        echo "Running unit tests for ${SERVICE_NAME}..."
        pip3 install --user --no-cache-dir uv
        uv sync
        uv run pytest ${UNIT_TEST_FILE}
        '''
      }
    }

    stage('BUILD AND PUSH DOCKER IMAGE') {
      when {
        anyOf {
          branch 'main'
          branch 'dev'
        }
      }
      steps {
        script {
          def BRANCH_NAME = env.BRANCH_NAME
          def imageTag = "${ECR_REPO}:${SERVICE_NAME}-${BRANCH_NAME}-${BUILD_ID}"
          sh """
          #!/bin/bash
          set -e
          echo "Building Docker image for ${SERVICE_NAME}..."
          docker build -t ${imageTag} .
          echo "Authenticating to ECR..."
          aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
          echo "Pushing Docker image to ECR..."
          docker push ${imageTag}
          echo "✅ Image pushed successfully: ${imageTag}"
          """
        }
      }
    }
  }

  post {
    always {
      cleanWs()
    }
    failure {
      echo "❌ Build failed for ${SERVICE_NAME} on ${BRANCH_NAME}"
    }
  }
}
