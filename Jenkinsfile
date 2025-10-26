pipeline {
  agent any

  environment {
    SERVICE_NAME = 'order-service'
    ECR_REPO = '359672545978.dkr.ecr.ap-southeast-1.amazonaws.com/icetea/microservices'
    UNIT_TEST_FILE = 'test_app.py'
  }

  stages {
    stage('RUN UNIT TESTS') {
      when {
        changeRequested()
      }
      steps {
        checkout scm
        sh '''
        #!/bin/bash
        set -e
        echo "Running unit tests for ${SERVICE_NAME}..."
        pip3 install uv
        uv sync
        uv run pytest ${UNIT_TEST_FILE}
        '''
      }
    }
  }
}
