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
      post {
        success {
          echo "✅ Unit tests passed for ${SERVICE_NAME}"
        }
        failure {
          echo "❌ Unit tests failed for ${SERVICE_NAME}"
        }
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
          def COMMIT_ID = env.GIT_COMMIT.substring(0, 7)
          def imageTag = "${ECR_REPO}:${SERVICE_NAME}-${BRANCH_NAME}-${COMMIT_ID}"
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
      post {
        always {
          script {
            sh 'docker system prune -a -f --volumes'
            echo "✅ Cleaned up all Docker resources"
          }
        }
        success {
          script {
            def BRANCH_NAME = env.BRANCH_NAME
            echo "✅ Build and push completed for ${SERVICE_NAME} on ${BRANCH_NAME}"
          }
        }
        failure {
          script {
            def BRANCH_NAME = env.BRANCH_NAME
            echo "❌ Build or push failed for ${SERVICE_NAME} on ${BRANCH_NAME}"
          }
        }
      }
    }

    stage('DEPLOY TO AWS EC2') {
      when {
        anyOf {
          branch 'main'
          branch 'dev'
        }
      }
      steps {
        script {
          def BRANCH_NAME = env.BRANCH_NAME
          def SERVER_IP = (BRANCH_NAME == 'main') ? '52.221.208.1' : '13.212.126.70'
          def SSH_KEY_ID = 'ssh-private-key'
          def COMMIT_ID = env.GIT_COMMIT.substring(0, 7)

          echo "🚀 Deploying ${SERVICE_NAME} to ${BRANCH_NAME} server (${SERVER_IP})..."

          sshagent([SSH_KEY_ID]) {
            sh """
            #!/bin/bash
            set -e
            ssh -o StrictHostKeyChecking=no ec2-user@${SERVER_IP} << 'ENDSSH'
              aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
              docker pull ${ECR_REPO}:${SERVICE_NAME}-${BRANCH_NAME}-${COMMIT_ID}
              docker stop ${SERVICE_NAME} || true
              docker rm ${SERVICE_NAME} || true
              docker run -d --name ${SERVICE_NAME} -p 5000:5000 ${ECR_REPO}:${SERVICE_NAME}-${BRANCH_NAME}-${COMMIT_ID}
              echo "✅ Deployed ${SERVICE_NAME} on server ${SERVER_IP}"
            ENDSSH
            """
          }
        }
      }
    }
  }

  post {
    always {
      cleanWs()
    }
    failure {
      script {
        def BRANCH_NAME = env.BRANCH_NAME
        echo "❌ Build failed for ${SERVICE_NAME} on ${BRANCH_NAME}"
      }
    }
  }
}

