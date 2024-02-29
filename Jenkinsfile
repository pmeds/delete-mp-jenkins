pipeline {
  agent any
  stages {
    stage('Get excel and python script') {
      steps {
        echo 'Getting the excel and python files'
        sh '''ls -la
chmod 754 CSV_formatter.py
chmod 754 staging_mp_delete_rules.py'''
      }
    }

    stage('Running formatter') {
      steps {
        echo 'Running CSV formatter and generating CSV files'
        sh 'python3 CSV_formatter.py'
        sh 'ls -la'
      }
    }

    stage('Upload Games') {
      steps {
        echo 'checking if there is a csv file for games'
        script {
          if (fileExists('delete-test-games-upload.csv')) {
            sh 'echo "uploading games rules"'
            sh 'python3 staging_mp_delete_rules.py delete-test-games-upload.csv'
          }
        }

      }
    }

    stage('Upload General') {
      steps {
        echo 'Checking for CSV for General'
        script {
          if (fileExists('delete-test-general-upload.csv')) {
            sh 'echo "uploading general rules"'
            sh 'python3 staging_mp_delete_rules.py delete-test-general-upload.csv'
          }
        }

      }
    }

    stage('Delete environment') {
      steps {
        cleanWs(cleanWhenAborted: true, cleanWhenFailure: true, cleanWhenNotBuilt: true, cleanWhenSuccess: true)
      }
    }

  }
}
