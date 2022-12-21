node ("rhel-large") {
    deleteDir()
    def pomVersion
    def pomProjectName
    def descriptorsFile = "descriptors.csv"
    ...

    stage ("prepare") {
        sh 'touch ~/.ssh/known_hosts'

        dir("workdir") {
            ...
            pom = readMavenPom file: 'pom.xml'
            pomVersion = pom.version
            pomProjectName = pom.artifactId
        }
    }

    stage ("build") {
        timeout(time: 2, unit: 'HOURS') {
            dir("workdir") {
                withMaven(...)
        }
    }

    stage("compute-manifest") {
        dir("workdir") {
            // Build descriptor file
            withMaven(jdk: 'OpenJDK 1.8.0 (latest)', maven: 'Maven 3.5 (latest)', mavenLocalRepo: '${WORKSPACE}/.repository', mavenOpts: '-Dsettings.security=${WORKSPACE}/.repository/settings-security.xml',
                        mavenSettingsConfig: 'CHANGEME') {
                configFileProvider([
                    configFile(fileId: 'CHANGEME',
                    targetLocation: "${WORKSPACE}/.repository/settings-security.xml")
                    ]) {
                        sh "mvn -Dexec.executable=echo -Dexec.args='\${project.artifactId},\${project.name},\${project.version}' --quiet exec:exec > ${descriptorsFile}"
                }
            }

            // Copy file into separate folder
            sh """
                mkdir upload
                cp features/*/target/*.dp ./upload
                cp bundles/*/target/*.jar ./upload
                cp bundles/*/target/*.dp ./upload
                cp RELEASE_NOTES.txt ./upload/RELEASE_NOTES_${pomProjectName}_${pomVersion}.txt
            """

            // Download and run python script
            sh """
                curl wget https://raw.githubusercontent.com/eurotech/add-ons-automation/feat/manifest_builder/config/manifest_builder/manifest_builder.py --output manifest_builder
                python3 manifest_builder.py -f ./upload -v ${pomVersion} -n ${pomProjectName} -b ${BUILD_NUMBER} -c ${descriptorsFile}
            """
        }
    }

    stage("deploy-s3") {
        if (PUSH_ARTIFACTS.toBoolean()) {
            withAWS(credentials: 'CHANGEME', region: 'CHANGEME') {
                dir("workdir") {
                    files = findFiles(glob: './upload/*')
                    files.each {
                        println "FILE:  ${it}"
                        s3Upload acl: 'Private', bucket: 'eth-repo', file: "${it}", metadatas: [''], path: "esf-bundles/${pomProjectName}/${pomVersion}_${BUILD_NUMBER}/"
                    }
                }
            }
        } else {
            echo "Skipping publish artifacts"
        }
    }
}
