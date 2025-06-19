pipeline {
	agent any

	environment {
		DOCKER_IMAGE = 'ml-research-agent'
		DOCKER_TAG = '${BUILD_NUMBER}'
	}

	stages {
		stage('Checkout') {
			steps {
				checkout scm
			}
		}

		stage('Build Docker Image') {
			steps {
				script {
					sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
				}
			}
		}

		stage('Deploy') {
			when {
				branch 'main'
			}

			steps {
				script {
					sh """
						docker stop ${DOCKER_IMAGE} || true
						docker remove ${DOCKER_IMAGE} || true
						docker run -d --name ${DOCKER_IMAGE} -p 8001:8001 ${DOCKER_IMAGE}:${DOCKER_TAG}
					"""
				}
			}
		}
	}

	post {
		always {
			sh "docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true"
		}
	}
}
