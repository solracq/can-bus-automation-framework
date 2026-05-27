pipeline {
  agent any

  parameters {
    choice(
      name: 'INTEGRATION_BACKEND',
      choices: ['virtual', 'socketcan', 'socketcan-privileged'],
      description: 'Use virtual for macOS/Windows Jenkins, socketcan for Linux agents with vcan support.'
    )
  }

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

    stage('Integration Tests') {
      steps {
        script {
          def command

          if (params.INTEGRATION_BACKEND == 'virtual') {
            command = '''
              docker run --rm \
                -e RUN_VCAN_TESTS=1 \
                -e CAN_CHANNEL="virtual-can" \
                -e CAN_INTERFACE=virtual \
                "${TEST_IMAGE}" \
                pytest -q -m integration
            '''
          } else {
            def privilegeFlag = params.INTEGRATION_BACKEND == 'socketcan-privileged'
              ? '--privileged'
              : '--cap-add=NET_ADMIN'

            command = """
              docker run --rm \
                ${privilegeFlag} \
                -e RUN_VCAN_TESTS=1 \
                -e CAN_CHANNEL="${CAN_CHANNEL}" \
                -e CAN_INTERFACE="${CAN_INTERFACE}" \
                "${TEST_IMAGE}" \
                pytest -q -m integration
            """
          }

          sh command
        }
      }
    }
  }

  post {
    always {
      sh 'docker image rm -f "${TEST_IMAGE}" || true'
    }
  }
}
