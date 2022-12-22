node ("rhel-large") {
    deleteDir()
    def pomVersion
    def pomArtifactId

    def descriptorsFile = "descriptors.csv"
    def uploadDirectory = "upload"
    ...

    stage ("prepare") {
        sh 'touch ~/.ssh/known_hosts'

        dir("workdir") {
            ...
            pom = readMavenPom file: 'pom.xml'
            pomVersion = pom.version
            pomArtifactId = pom.artifactId
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

            // Remove undesired output from CSV file
            sh """
                sed -i "/:/d" ${descriptorsFile}
                sed -i "/-----/d" ${descriptorsFile}
            """

            // Copy file into separate folder
            sh """
                mkdir ${uploadDirectory}
                cp features/*/target/*.dp ${uploadDirectory} # NOTE: Example only! Refer to original Jenkins configuration
                cp bundles/*/target/*.jar ${uploadDirectory} # NOTE: Example only! Refer to original Jenkins configuration
                cp RELEASE_NOTES.txt ${uploadDirectory}/RELEASE_NOTES_${pomArtifactId}_${pomVersion}.txt
            """

            // Download and run python script
            sh """
                curl https://raw.githubusercontent.com/eurotech/add-ons-automation/main/config/manifest_builder/manifest_builder.py --output manifest_builder.py
                python3 manifest_builder.py -f ${uploadDirectory} -v ${pomVersion} -n ${pomArtifactId} -b ${BUILD_NUMBER} -c ${descriptorsFile}
            """
        }
    }

    stage("deploy-s3") {
        if (PUSH_ARTIFACTS.toBoolean()) {
            withAWS(credentials: 'CHANGEME', region: 'CHANGEME') {
                dir("workdir") {
                    def file_path = "${uploadDirectory}/*"
                    files = findFiles(glob: file_path)
                    files.each {
                        println "FILE:  ${it}"
                        s3Upload acl: 'Private', bucket: 'eth-repo', file: "${it}", metadatas: [''], path: "esf-bundles/${pomArtifactId}/${pomVersion}_${BUILD_NUMBER}/"
                    }
                }
            }
        } else {
            echo "Skipping publish artifacts"
        }
    }
}
