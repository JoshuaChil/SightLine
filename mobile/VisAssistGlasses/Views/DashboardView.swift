//
//  DashboardView.swift
//  VisAssistGlasses
//
//  Created by Trevor Bedson on 6/18/25.
//

import SwiftUI

struct DashboardView: View {
    var body: some View {
        VStack {
            Text("Dashboard")
                .frame(maxWidth: .infinity, alignment: .leading)
                .font(.title)
                .fontWeight(.semibold)
                .foregroundStyle(.white)
            
            Spacer()
        }
        .padding(.horizontal, 20)
    }
}

#Preview {
    DashboardView()
}
