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

        # Install wrapper + pytest + reporters into ~/.local so no sudo.
        # If install fails, we want to stop early (set -e above).
        pip3 install --user --no-cache-dir uv pytest pytest-cov pytest-html allure-pytest

        # sync with uv if you're using it (keeps your workflow)
        pip3 show uv >/dev/null 2>&1 && uv sync || true

        # Run tests but don't let the shell exit the whole step on failure:
        # - produce junit xml, html report, allure-results, coverage xml
        # - tee to both console and a log file
        # - capture pytest exit code (so we can publish reports even if tests fail)
        set +e
        uv --version >/dev/null 2>&1 && RUN_CMD='uv run pytest' || RUN_CMD='pytest'
        echo "Using test command: $RUN_CMD"
        # run pytest with reporters
        $RUN_CMD -v -s ${UNIT_TEST_FILE} \
          --junitxml=pytest-report.xml \
          --alluredir=allure-results \
          --cov=./ --cov-report=xml:coverage.xml \
          --html=pytest-report.html --self-contained-html \
          2>&1 | tee pytest.log
        PYTEST_EXIT=${PIPESTATUS[0]}
        echo "Pytest exit code: ${PYTEST_EXIT}"
        # keep step successful so post { always } can run junit/publish steps;
        # junit step will mark the build failed/unstable based on XML contents.
        set -e
        exit 0
        '''
      }
      post {
        success {
          echo "✅ Unit tests step completed for ${SERVICE_NAME} (check Test Results)."
        }
        failure {
          echo "⚠️ Unit tests step failed to run (installation or unexpected error)."
        }
        always {
          // publish junit results -> Jenkins Test Results page + trend + failures list
          junit allowEmptyResults: true, testResults: 'pytest-report.xml'

          // publish pytest-html report (requires HTML Publisher plugin)
          publishHTML (target: [
            reportDir: '.', 
            reportFiles: 'pytest-report.html', 
            reportName: 'Pytest HTML Report', 
            keepAll: true, 
            alwaysLinkToLastBuild: true
          ])

          // archive raw artifacts and allure results for Allure plugin
          archiveArtifacts artifacts: 'pytest.log, pytest-report.xml, pytest-report.html, coverage.xml, allure-results/**', fingerprint: true

          // optional: if you have Allure Jenkins plugin installed, the separate 'Allure' publisher step
          // can be added in a follow-up stage to render interactive Allure report:
          // allure([
          //   results: [[path: 'allure-results']],
          //   reportBuildPolicy: 'ALWAYS'
          // ])
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

