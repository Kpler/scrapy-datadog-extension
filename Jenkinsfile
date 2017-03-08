node {
    try {
        notifyStarted()
        
        // Checkout code from repository
        stage 'Checkout'
            checkout scm

        stage 'Build'
            echo "Building ${BRANCH_NAME}"
            sh 'chmod +x runtests.sh'
            sh './runtests.sh'
        
        notifySuccessful()
    } catch(e) {
        currentBuild.result = "FAILED"
        notifyFailed()
        throw e
    }
}

def notifyStarted() {
    slackSend (color: '#FFFF00', message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
}

def notifySuccessful() {
    slackSend (color: '#00FF00', message: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
}

def notifyFailed() {
    slackSend (color: '#FF0000', message: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
}
