node {
    // Checkout code from repository
    stage 'Checkout'
        checkout scm

    stage 'Build'
        echo "Building ${BRANCH_NAME}"
        sh 'chmod +x runtests.sh'
        sh './runtests.sh'
    
    stage 'Notify'
        slackSend (color: '#FFFF00', message: "STARTED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
}
