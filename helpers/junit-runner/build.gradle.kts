plugins {
    id("java")
}

group = "org.pastalab.fray.helpers"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}


dependencies {
    implementation("org.junit.jupiter:junit-jupiter-engine:5.10.2")
    implementation("org.junit.vintage:junit-vintage-engine:5.10.2")
    implementation("org.junit.platform:junit-platform-launcher:1.10.3")
}

tasks.test {
    useJUnitPlatform()
}


tasks.named("build") {
  finalizedBy("copyDependencies")
}

tasks.register<Copy>("copyDependencies") {
    from(configurations.runtimeClasspath)
    into("${layout.buildDirectory.get().asFile}/dependency")
}
