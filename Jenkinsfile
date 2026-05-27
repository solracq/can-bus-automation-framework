pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    TEST_IMAGE = "can-bus-automation-framework-tests:${BUILD_NUMBER}"
    CAN_CHANNEL = 'vcan0'
    CAN_INTERFACE = 'socketcan'
  }

  stages {
    stage('Build Test Image') {
      steps {
        sh 'docker build -t "${TEST_IMAGE}" .'
      }
    }

    stage('Smoke And Unit Tests') {
      steps {
        sh 'docker run --rm "${TEST_IMAGE}" pytest -q -m "smoke or unit"'
      }
    }

    stage('SocketCAN Integration Tests') {
      steps {
        sh '''
          docker run --rm \
            --cap-add=NET_ADMIN \
            -e RUN_VCAN_TESTS=1 \
            -e CAN_CHANNEL="${CAN_CHANNEL}" \
            -e CAN_INTERFACE="${CAN_INTERFACE}" \
            "${TEST_IMAGE}" \
            pytest -q -m integration
        '''
      }
    }
  }

  post {
    always {
      sh 'docker image rm -f "${TEST_IMAGE}" || true'
    }
  }
}
