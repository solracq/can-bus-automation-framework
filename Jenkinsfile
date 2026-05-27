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
    stage('Prepare Artifacts') {
      steps {
        sh '''
          rm -rf artifacts
          mkdir -p artifacts/junit artifacts/logs
        '''
      }
    }

    stage('Build Test Image') {
      steps {
        sh 'docker build -t "${TEST_IMAGE}" .'
      }
    }

    stage('Smoke And Unit Tests') {
      steps {
        sh '''
          docker run --rm \
            -v "$PWD/artifacts:/artifacts" \
            -e PYTEST_LOG_DIR=/artifacts/logs \
            -e PYTEST_LOG_FILE=smoke-unit.log \
            "${TEST_IMAGE}" \
            pytest -q -m "smoke or unit" --junitxml=/artifacts/junit/smoke-unit.xml
        '''
      }
    }

    stage('Integration Tests') {
      steps {
        script {
          def command
          def fileBase

          if (params.INTEGRATION_BACKEND == 'virtual') {
            fileBase = 'integration-virtual'
            command = '''
              docker run --rm \
                -v "$PWD/artifacts:/artifacts" \
                -e RUN_VCAN_TESTS=1 \
                -e PYTEST_LOG_DIR=/artifacts/logs \
                -e PYTEST_LOG_FILE=integration-virtual.log \
                -e CAN_CHANNEL="virtual-can" \
                -e CAN_INTERFACE=virtual \
                "${TEST_IMAGE}" \
                pytest -q -m integration --junitxml=/artifacts/junit/integration-virtual.xml
            '''
          } else {
            def privilegeFlag = params.INTEGRATION_BACKEND == 'socketcan-privileged'
              ? '--privileged'
              : '--cap-add=NET_ADMIN'
            fileBase = params.INTEGRATION_BACKEND == 'socketcan-privileged'
              ? 'integration-socketcan-privileged'
              : 'integration-socketcan'

            command = """
              docker run --rm \
                ${privilegeFlag} \
                -v "\$PWD/artifacts:/artifacts" \
                -e RUN_VCAN_TESTS=1 \
                -e PYTEST_LOG_DIR=/artifacts/logs \
                -e PYTEST_LOG_FILE=${fileBase}.log \
                -e CAN_CHANNEL="${CAN_CHANNEL}" \
                -e CAN_INTERFACE="${CAN_INTERFACE}" \
                "${TEST_IMAGE}" \
                pytest -q -m integration --junitxml=/artifacts/junit/${fileBase}.xml
            """
          }

          sh command
        }
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'artifacts/junit/*.xml'
      archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts/**/*'
      sh 'docker image rm -f "${TEST_IMAGE}" || true'
    }
  }
}
