node {
    // Checkout code from repository
    stage 'Checkout'
        checkout scm

    stage 'Build' {}
        echo "Building ${BRANCH_NAME}"
        sh 'chmod +x runtests.sh'
        sh './runtests.sh'
}
