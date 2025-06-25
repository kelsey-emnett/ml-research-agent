pipeline {
	agent any

	environment {
		DOCKER_IMAGE = 'ml-research-agent'
		DOCKER_TAG = '${BUILD_NUMBER}'
		CONFIG_DIR = "${WORKSPACE}/config"
	}

	stages {
		stage('Checkout') {
			steps {
				checkout scm
			}
		}

		stage('Setup Config') {
			steps {
				script {
					sh "mkdir -p ${CONFIG_DIR}"

					sh "cp config.yaml ${CONFIG_DIR}/ || true"
				}
			}
		}

		stage('Add Environment Variables') {
			steps {
				withCredentials([file(credentialsId: 'env-file', variable: 'ENV_FILE')]) {
					sh 'cp $ENV_FILE .env'
				}
			}
		}


		stage('Build Docker Image') {
			steps {
				script {
					sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
				}
			}
		}

		stage('Test') {
			steps {
				script {
					sh """
						docker run --rm \
						--env-file .env \
						-v ${CONFIG_DIR}:/app/config \
						${DOCKER_IMAGE}:${DOCKER_TAG} pytest
					"""
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
						docker run -d --name ${DOCKER_IMAGE} \
						 --env-file .env \
						 -v ${CONFIG_DIR}:/app/config \
						 -p 8001:8001 ${DOCKER_IMAGE}:${DOCKER_TAG}
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
