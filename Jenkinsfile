pipeline {
  agent any
  stages {
    stage('Get excel and python script') {
      steps {
        echo 'Getting the excel and python files'
        sh '''ls -la
chmod 754 CSV_formatter.py
chmod 754 staging_mp_delete_rules.py
chmod 754 staging_delete_validation.py 
'''
      }
    }

    stage('Running formatter') {
      steps {
        echo 'Running CSV formatter and generating CSV files'
        sh 'python3 CSV_formatter.py'
        sh 'ls -la'
      }
    }

    stage('Delete Rules') {
      steps {
        echo 'checking if there is a csv file for games'
        script {
          if (fileExists('delete-test-upload.csv')) {
            sh 'echo "uploading games rules"'
            sh 'python3 staging_mp_delete_rules.py delete-test-upload.csv'
          }
        }

      }
    }

    stage('Testing All Redirects') {
      steps {
        echo 'Testing the deleted rules'
        script {
          if (fileExists('delete-test-upload.csv')) {
            sh 'echo "testing uploaded general rules"'
            sh 'python3 paul_staging_mp_redir_validation.py'
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
