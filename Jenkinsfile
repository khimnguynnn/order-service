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
      when { changeRequest() }
      steps {
        sh '''
        #!/bin/bash
        set -e
        export PATH=$PATH:$HOME/.local/bin
        echo "Running unit tests for ${SERVICE_NAME}..."

        # activate venv if exists
        if [ -d ".venv" ]; then
          echo "Activating .venv"
          source .venv/bin/activate
        fi

        # install pytest + plugins into the active interpreter (venv or agent py)
        pip install -r requirements.txt
        pip install --no-cache-dir pytest pytest-cov pytest-html allure-pytest

        # run pytest and produce reports; capture exit code but don't fail shell so we can publish results
        set +e
        python3 -m pytest -v -s ${UNIT_TEST_FILE} \
          --junitxml=pytest-report.xml \
          --alluredir=allure-results \
          --cov=./ --cov-report=xml:coverage.xml \
          --html=pytest-report.html --self-contained-html \
          2>&1 | tee pytest.log
        PYTEST_EXIT=${PIPESTATUS[0]}
        echo "Pytest exit code: ${PYTEST_EXIT}"
        set -e
        exit 0
        '''
      }

      post {
        always {
          junit allowEmptyResults: true, testResults: 'pytest-report.xml'
          publishHTML (target: [
            reportDir: '.',
            reportFiles: 'pytest-report.html',
            reportName: 'Pytest HTML Report',
            keepAll: true,
            alwaysLinkToLastBuild: true
          ])
          archiveArtifacts artifacts: 'pytest.log, pytest-report.xml, pytest-report.html, coverage.xml, allure-results/**', fingerprint: true
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
          def SERVER_IP = (BRANCH_NAME == 'main') ? '52.221.180.12' : '13.212.118.127'
          def SSH_KEY_ID = 'ssh-private-key'
          def COMMIT_ID = env.GIT_COMMIT.substring(0, 7)

          echo "🚀 Deploying ${SERVICE_NAME} to ${BRANCH_NAME} server (${SERVER_IP})..."
          sh 'echo ${COMMIT_ID} > /tmp/last_deployed_commit.txt'
            sshagent([SSH_KEY_ID]) {
              sh """
              #!/bin/bash
              set -e
              ssh -o StrictHostKeyChecking=no ec2-user@${SERVER_IP} '
                aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
                docker pull ${ECR_REPO}:${SERVICE_NAME}-${BRANCH_NAME}-${COMMIT_ID}
                docker stop ${SERVICE_NAME} || true
                docker rm ${SERVICE_NAME} || true
                docker run -d -e ENVIRONMENT=${BRANCH_NAME} --name ${SERVICE_NAME} -p 5000:5000 ${ECR_REPO}:${SERVICE_NAME}-${BRANCH_NAME}-${COMMIT_ID}
                sudo nginx -t && sudo nginx -s reload || echo "Nginx reload failed, but deployment completed"
                echo "✅ Deployed ${SERVICE_NAME} on server ${SERVER_IP}"
              '
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

